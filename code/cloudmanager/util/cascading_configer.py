# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import time
from heat.openstack.common import log as logging

import commonutils
import constant
import cloud_manager_exception
LOG = logging.getLogger(__name__)

class CascadingConfiger(object):
    def __init__(self, cascading_ip, user, password, cascaded_domain,
                 cascaded_api_ip, v2v_gw):
        self.cascading_ip = cascading_ip
        self.user = user
        self.password = password
        self.cascaded_domain = cascaded_domain
        self.cascaded_ip = cascaded_api_ip
        self.v2v_gw = v2v_gw

    def do_config(self):
        start_time = time.time()
        LOG.info("start config cascading, cascading: %s" % self.cascading_ip)

        # modify dns server address
        address = "/%(cascaded_domain)s/%(cascaded_ip)s" \
                  % {"cascaded_domain": self.cascaded_domain,
                     "cascaded_ip": self.cascaded_ip}

        for i in range(3):
            try:
                commonutils.execute_cmd_without_stdout(
                    host=self.cascading_ip,
                    user=self.user,
                    password=self.password,
                    cmd='cd %(dir)s; sh %(script)s add %(address)s'
                        % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                           "script": constant.PublicConstant.
                               MODIFY_DNS_SERVER_ADDRESS,
                           "address": address})
                break
            except exception.SSHCommandFailure as e:
                LOG.error("modify cascading dns address error, cascaded: "
                             "%s, error: %s"
                             % (self.cascaded_domain, e.format_message()))
                time.sleep(1)

        LOG.info(
            "config cascading dns address success, cascading: %s"
            % self.cascading_ip)

        # config keystone
        for i in range(3):
            try:
                commonutils.execute_cmd_without_stdout(
                    host=self.cascading_ip,
                    user=self.user,
                    password=self.password,
                    cmd='cd %(dir)s;'
                        'sh %(script)s %(cascaded_domain)s'
                        % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                           "script":
                               constant.RemoveConstant.REMOVE_KEYSTONE_SCRIPT,
                           "cascaded_domain": self.cascaded_domain})

                commonutils.execute_cmd_without_stdout(
                    host=self.cascading_ip,
                    user=self.user,
                    password=self.password,
                    cmd='cd %(dir)s;'
                        'sh %(script)s %(cascaded_domain)s %(v2v_gw)s'
                        % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                           "script":
                               constant.Cascading.KEYSTONE_ENDPOINT_SCRIPT,
                           "cascaded_domain": self.cascaded_domain,
                           "v2v_gw": self.v2v_gw})
                break
            except exception.SSHCommandFailure as e:
                LOG.error(
                    "create keystone endpoint error, cascaded: %s, error: %s"
                    % (self.cascaded_domain, e.format_message()))
                time.sleep(1)

        LOG.info("config cascading keystone success, cascading: %s"
                    % self.cascading_ip)

        for i in range(3):
            try:
                commonutils.execute_cmd_without_stdout(
                    host=self.cascading_ip,
                    user=self.user,
                    password=self.password,
                    cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                        % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                           "script":
                               constant.Cascading.ENABLE_OPENSTACK_SERVICE,
                           "cascaded_domain": self.cascaded_domain})
                break
            except exception.SSHCommandFailure as e:
                LOG.error(
                    "enable openstack service error, cascaded: %s, error: %s"
                    % (self.cascaded_domain, e.format_message()))
                time.sleep(1)

        LOG.info("enable openstack service success, cascading: %s"
                    % self.cascading_ip)
        cost_time = time.time() - start_time
        LOG.info("config cascading success, cascading: %s, cost time: %d"
                    % (self.cascading_ip, cost_time))
