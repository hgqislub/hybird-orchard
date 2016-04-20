# Copyright 2012 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Wrapper for keystone.common.config that configures itself on import."""

import os

from oslo.config import cfg
from oslo.db import options

from cms import paths
from cms import rpc
import version


_DEFAULT_SQL_CONNECTION = 'sqlite:///' + paths.state_path_def('cms.sqlite')

CONF = cfg.CONF

opts = [
    cfg.IntOpt('cms_port',
               default=7027, help='Port of cms rest service.'),
    cfg.StrOpt('fs_gateway_url',
        default='http://127.0.0.1:7027/v1.0', help='Url of fs gateway rest url.'),
    ]

CONF.register_opts(opts)


def parse_args(argv, default_config_files=None):
    options.set_defaults(CONF, connection=_DEFAULT_SQL_CONNECTION,
                         sqlite_db='cms.sqlite')
    rpc.set_defaults(control_exchange='cms')
    CONF(argv[1:],
         project='cms',
         version=version.version_string(),
         default_config_files=default_config_files)
    rpc.init(CONF)
    for key in ('cascading_admin_password', 'cascaded_admin_password'):
        if key in CONF:
            password = CONF[key]

            try:
                from FSComponentUtil import crypt
                CONF.set_override(key, crypt.decrypt(password))
            except Exception:
                pass

