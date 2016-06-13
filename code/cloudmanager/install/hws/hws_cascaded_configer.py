# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import time
from heat.openstack.common import log as logging

import heat.engine.resources.cloudmanager.commonutils as commonutils
import heat.engine.resources.cloudmanager.constant as constant
import heat.engine.resources.cloudmanager.exception as exception
import pdb

LOG = logging.getLogger(__name__)


class CascadedConfiger(object):
    def __init__(self, public_ip_api, api_ip, domain, user, password,
                 cascading_domain, cascading_api_ip, cascaded_domain,
                 cascaded_api_ip, cascaded_api_subnet_gateway):
        self.public_ip_api = public_ip_api
        self.api_ip = api_ip
        self.domain = domain
        self.user = user
        self.password = password
        self.cascading_domain = cascading_domain
        self.cascading_api_ip = cascading_api_ip
        self.cascaded_domain = cascaded_domain
        self.cascaded_ip = cascaded_api_ip
        self.gateway = cascaded_api_subnet_gateway

    def do_config(self):
        start_time = time.time()
        #pdb.set_trace()
        LOG.info("start config cascaded, cascaded: %s" % self.domain)
        # wait cascaded tunnel can visit
        commonutils.check_host_status(host=self.public_ip_api,
                                      user=self.user,
                                      password=self.password,
                                      retry_time=500, interval=1)

        # config cascaded host
        self._config_az_cascaded()

        cost_time = time.time() - start_time
        LOG.info("first config success,  cascaded: %s, cost time: %d"
                    % (self.domain, cost_time))

        # check config result
        for i in range(3):
            try:
                # check 90s
                commonutils.check_host_status(
                    host=self.public_ip_api,
                    user=constant.VcloudConstant.ROOT,
                    password=constant.VcloudConstant.ROOT_PWD,
                    retry_time=15,
                    interval=1)
                LOG.info("cascaded api is ready..")
                break
            except exception.CheckHostStatusFailure:
                if i == 2:
                    LOG.error("check cascaded api failed ...")
                    break
                LOG.error("check cascaded api error, "
                             "retry config cascaded ...")
                self._config_az_cascaded()

        cost_time = time.time() - start_time
        LOG.info("config cascaded success, cascaded: %s, cost_time: %d"
                    % (self.domain, cost_time))

    def _config_az_cascaded(self):
        LOG.info("start config cascaded host, host: %s" % self.api_ip)
        # modify dns server address
        address = "/%(cascading_domain)s/%(cascading_ip)s,/%(cascaded_domain)s/%(cascaded_ip)s" \
                  % {"cascading_domain": self.cascading_domain,
                     "cascading_ip": self.cascading_api_ip,
                     "cascaded_domain":self.cascaded_domain,
                     "cascaded_ip":self.cascaded_ip}
        for i in range(30):
            try:
                commonutils.execute_cmd_without_stdout(
                    host=self.public_ip_api,
                    user=self.user,
                    password=self.password,
                    cmd='cd %(dir)s; source /root/adminrc; sh %(script)s replace %(address)s'
                        % {"dir": constant.PublicConstant.SCRIPTS_DIR,
                           "script": constant.PublicConstant.
                               MODIFY_DNS_SERVER_ADDRESS,
                           "address": address})
                break
            except exception.SSHCommandFailure as e:
                LOG.error("modify cascaded dns address error, cascaded: "
                             "%s, error: %s"
                             % (self.domain, e.format_message()))
                time.sleep(1)

        LOG.info(
            "config cascaded dns address success, cascaded: %s"
            % self.public_ip_api)

        return True


