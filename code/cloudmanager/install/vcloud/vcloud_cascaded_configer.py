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
                 cascading_domain, cascading_api_ip):
        self.public_ip_api = public_ip_api
        self.api_ip = api_ip
        self.domain = domain
        self.user = user
        self.password = password
        self.cascading_domain = cascading_domain
        self.cascading_api_ip = cascading_api_ip

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

        time.sleep(20)

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
        #pdb.set_trace()
        gateway = _get_gateway(self.api_ip)
        for i in range(30):
            try:
                commonutils.execute_cmd_without_stdout(
                    host=self.public_ip_api,
                    user=constant.VcloudConstant.ROOT,
                    password=constant.VcloudConstant.ROOT_PWD,
                    cmd='cd %(dir)s; python %(script)s '
                        '%(cascading_domain)s %(cascading_api_ip)s '
                        '%(cascaded_domain)s %(cascaded_ip)s '
                        '%(gateway)s'
                        % {"dir": constant.Cascaded.REMOTE_VCLOUD_SCRIPTS_DIR,
                           "script":
                               constant.Cascaded.MODIFY_CASCADED_SCRIPT_PY,
                           "cascading_domain": self.cascading_domain,
                           "cascading_api_ip": self.cascading_api_ip,
                           "cascaded_domain": self.domain,
                           "cascaded_ip": self.api_ip,
                           "gateway": gateway})
                break
            except exception.SSHCommandFailure as e:
                LOG.error("modify cascaded domain error: %s"
                             % e.message)
                time.sleep(5)
        return True


def _get_gateway(ip, mask=None):
    arr = ip.split(".")
    gateway = "%s.%s.%s.1" % (arr[0], arr[1], arr[2])
    return gateway
