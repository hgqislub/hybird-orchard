# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Implementation of SQLAlchemy backend."""

import collections
import copy
import datetime
import functools
import sys
import threading
import time
import uuid

from oslo.config import cfg
from oslo.db import exception as db_exc
from oslo.db.sqlalchemy import session as db_session
from oslo.db.sqlalchemy import utils as sqlalchemyutils
import six
from sqlalchemy import and_
from sqlalchemy import Boolean
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import or_
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import joinedload_all
from sqlalchemy.orm import noload
from sqlalchemy.orm import undefer
from sqlalchemy.schema import Table
from sqlalchemy import sql
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql.expression import desc
from sqlalchemy.sql import false
from sqlalchemy.sql import func
from sqlalchemy.sql import null
from sqlalchemy.sql import true
from sqlalchemy import String

import cms.context
from cms.db.sqlalchemy import models
from cms import exception
from cms.i18n import _
from cms.common import log as logging

db_opts = [
    cfg.StrOpt('cms_api_name_scope',
               default='',
               help='When set, compute API will consider duplicate hostnames '
                    'invalid within the specified scope, regardless of case. '
                    'Should be empty, "project" or "global".'),
]

CONF = cfg.CONF
CONF.register_opts(db_opts)

LOG = logging.getLogger(__name__)
# LOG.basicConfig(filename='myapp.log', level=LOG.INFO)


_ENGINE_FACADE = None
_LOCK = threading.Lock()


def _create_facade_lazily():
    global _LOCK, _ENGINE_FACADE
    if _ENGINE_FACADE is None:
        with _LOCK:
            if _ENGINE_FACADE is None:
                _ENGINE_FACADE = db_session.EngineFacade.from_config(CONF)
    return _ENGINE_FACADE


def get_engine(use_slave=False):
    facade = _create_facade_lazily()
    return facade.get_engine(use_slave=use_slave)


def get_session(use_slave=False, **kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(use_slave=use_slave, **kwargs)


_SHADOW_TABLE_PREFIX = 'shadow_'
_DEFAULT_QUOTA_NAME = 'default'


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def require_context(f):
    """Decorator to require *any* cloud or admin context.

    This does no authorization for cloud or project access matching, see
    :py:func:`cms.context.authorize_project_context` and
    :py:func:`cms.context.authorize_cloud_context`.

    The first argument to the wrapped function must be the context.

    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        cms.context.require_context(args[0])
        return f(*args, **kwargs)
    return wrapper


def require_aggregate_exists(f):
    """Decorator to require the specified aggregate to exist.

    Requires the wrapped function to use context and aggregate_id as
    their first two arguments.
    """

    @functools.wraps(f)
    def wrapper(context, aggregate_id, *args, **kwargs):
        aggregate_get(context, aggregate_id)
        return f(context, aggregate_id, *args, **kwargs)
    return wrapper


def _retry_on_deadlock(f):
    """Decorator to retry a DB API call if Deadlock was received."""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except db_exc.DBDeadlock:
                LOG.warn(_("Deadlock detected when running "
                           "'%(func_name)s': Retrying..."),
                           dict(func_name=f.__name__))
                # Retry!
                time.sleep(0.5)
                continue
    functools.update_wrapper(wrapped, f)
    return wrapped


def model_query(context, model, *args, **kwargs):
    """Query helper that accounts for context's `read_deleted` field.

    :param context: context to query under
    :param use_slave: If true, use slave_connection
    :param session: if present, the session to use
    :param read_deleted: if present, overrides context's read_deleted field.
    :param project_only: if present and context is cloud-type, then restrict
            query to match the context's project_id. If set to 'allow_none',
            restriction includes project_id = None.
    :param base_model: Where model_query is passed a "model" parameter which is
            not a subclass of CMSBase, we should pass an extra base_model
            parameter that is a subclass of CMSBase and corresponds to the
            model parameter.
    """

    use_slave = kwargs.get('use_slave') or False
    if CONF.database.slave_connection == '':
        use_slave = False

    session = kwargs.get('session') or get_session(use_slave=use_slave)
    read_deleted = kwargs.get('read_deleted') or context.read_deleted
    project_only = kwargs.get('hproject_only', False)

    def issubclassof_gw_base(obj):
        return isinstance(obj, type) and issubclass(obj, models.CMSBase)

    base_model = model
    if not issubclassof_gw_base(base_model):
        base_model = kwargs.get('base_model', None)
        if not issubclassof_gw_base(base_model):
            raise Exception(_("model or base_model parameter should be "
                              "subclass of CMSBase"))

    query = session.query(model, *args)

    default_deleted_value = base_model.__mapper__.c.deleted.default.arg
    if read_deleted == 'no':
        query = query.filter(base_model.deleted == default_deleted_value)
    elif read_deleted == 'yes':
        pass  # omit the filter to include deleted and active
    elif read_deleted == 'only':
        query = query.filter(base_model.deleted != default_deleted_value)
    else:
        raise Exception(_("Unrecognized read_deleted value '%s'")
                            % read_deleted)

    return query

###################

def _cloud_get(context, id, session=None, read_deleted='no'):
    result = model_query(context, models.Cloud, session=session, read_deleted='no').\
               filter_by(uuid=id).\
                first()
    if not result:
        raise exception.CloudNotFound(id = id)
    return result

@require_context
def cloud_get(context, id):
    try:
        result = _cloud_get(context, id)
    except db_exc.DBError:
        msg = _("Invalid Cloud id %s in request") % id
        LOG.warn(msg)
        raise exception.InvalidID(id=id)
    return result


@require_context
def cloud_create(context, values):
    cloud_ref = models.Cloud()
    cloud_ref.update(values)
    try:
        cloud_ref.save()
    except db_exc.DBDuplicateEntry as e:
        raise exception.CloudExists(region=values['region'], name=values['name'])
    except db_exc.DBReferenceError as e:
        raise exception.IntegrityException(msg=str(e))
    except db_exc.DBError as e:
        LOG.exception('DB error:%s', e)
        raise exception.CloudCreateFailed()
    return dict(cloud_ref)

@require_context
def cloud_update(context, id, values):
    session = get_session()
    with session.begin():
        cloud_ref = _cloud_get(context, id, session=session)
        if not cloud_ref:
            raise exception.CloudNotFound(id=id)
        new_region = values.get('region', cloud_ref.get('region', ''))
        new_name = values.get('name', cloud_ref.get('name', ''))
        cloud_ref.update(values)
        try:
            cloud_ref.save(session=session)
        except db_exc.DBDuplicateEntry:
            raise exception.CloudExists(region=new_region, name=new_name)

    return dict(cloud_ref)

@require_context
def cloud_get_all(context):
    clouds = model_query(context, models.Cloud).\
                     all()
    return [dict(r) for r in clouds ]

def cloud_delete(context, id):
    session = get_session()
    with session.begin():
        cloud_ref = _cloud_get(context, id, session=session)
        if not cloud_ref:
            raise exception.CloudNotFound(id=id)

        # result = model_query(context, models.ProjectAssociation, session=session, 
                               # read_deleted='no').\
                    # filter_by(cloudid=id).count()
        # if result > 0:
            # raise exception.CloudInUse(id=id)
        #cloud_ref.soft_delete(session=session)
        session.delete(cloud_ref)

