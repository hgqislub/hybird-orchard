"""Utilities and helper functions."""

import re

from cms import exception
from cms.i18n import _
from cms.common import jsonutils
from oslo.config import cfg
CONF = cfg.CONF


class LazyPluggable(object):
    """A pluggable backend loaded lazily based on some value."""

    def __init__(self, pivot, config_group=None, **backends):
        self.__backends = backends
        self.__pivot = pivot
        self.__backend = None
        self.__config_group = config_group

    def __get_backend(self):
        if not self.__backend:
            if self.__config_group is None:
                backend_name = CONF[self.__pivot]
            else:
                backend_name = CONF[self.__config_group][self.__pivot]
            if backend_name not in self.__backends:
                msg = _('Invalid backend: %s') % backend_name
                raise exception.GWException(msg)

            backend = self.__backends[backend_name]
            if isinstance(backend, tuple):
                name = backend[0]
                fromlist = backend[1]
            else:
                name = backend
                fromlist = backend

            self.__backend = __import__(name, None, None, fromlist)
        return self.__backend

    def __getattr__(self, key):
        backend = self.__get_backend()
        return getattr(backend, key)

class SmarterEncoder(jsonutils.json.JSONEncoder):
    """Help for JSON encoding dict-like objects."""
    def default(self, obj):
        if not isinstance(obj, dict) and hasattr(obj, 'iteritems'):
            return dict(obj.iteritems())
        return super(SmarterEncoder, self).default(obj)

def utf8(value):
    """Try to turn a string into utf-8 if possible.

    Code is directly from the utf8 function in
    http://github.com/facebook/tornado/blob/master/tornado/escape.py

    """
    if isinstance(value, unicode):
        return value.encode('utf-8')
    assert isinstance(value, str)
    return value


def get_value_from_dict(d, keys):
    """ return value from d in keys. """
    if not d:
        return None
    for k in keys:
        if k in d:
            return d[k]
        for v in d.values():
            if type(v) == dict:
                r = get_value_from_dict(v, keys)
                if r: return r
    return None

version_re = r'^/+(?P<version>v[-0-9.]+)'

def get_project_id(req):
    """ return project id from request. """

    path_info = req.environ.get('PATH_INFO')
    uuid='[0-9a-f]{32}'
    tenant_re = r'/(?P<tenant_id>%s)\b' % uuid
    m = re.match(version_re + '(' + tenant_re + ')', path_info)

    if m and m.group('tenant_id'):
        return m.group('tenant_id')
    return None
    return get_value_from_dict(req.environ.get('openstack.params'), 
                ["tenant_id", "project_id"])

def get_image_id(req):
    """ return image id from request. """

    uuid = '[-0-9a-zA-Z]+'
    image_re = r'/images/(?P<image_id>%s)' % uuid
    all_re = version_re + '(' +  image_re + ')'
    path_info = req.environ.get('PATH_INFO')
    m = re.match(all_re, path_info)
    if m and m.group('image_id'):
        return m.group('image_id')
    return get_value_from_dict(req.environ.get('openstack.params'), ["imageRef"])

def get_flavor_id(req):
    """ return flavor id from request. """

    """
    uuid='[-0-9a-zA-Z]+'
    flavor_re = r'/(?P<tenant_id>%s)/flavors/(?P<flavor_id>%s)' % (uuid, uuid)
    all_re = version_re + '(' +  flavor_re + ')'
    path_info = req.environ.get('PATH_INFO')
    m = re.match(all_re, path_info)
    if m and m.group('flavor_id'):
        return m.group('flavor_id')
    """
    return get_value_from_dict(req.environ.get('openstack.params'), ["flavorRef"])
