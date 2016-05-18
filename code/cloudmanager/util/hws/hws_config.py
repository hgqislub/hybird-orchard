
import sys
sys.path.append('..')

import os
import pdb
from heat.openstack.common import log as logging
import config_util as utils
from cloudmanager.vpn_configer import VpnConfiger
from cloudmanager.vpn import VPN
import cloudmanager.constant as constant
#import threading
import time
#import cloudmanager.proxy_manager
from cloudmanager.cascading_configer import CascadingConfiger
from hws_cascaded_configer import CascadedConfiger
from cloudmanager.commonutils import *
import cloudmanager.exception as exception
from cloud_manager_exception import *
from retry_decorator import RetryDecorator

LOG = logging.getLogger(__name__)
MAX_RETRY = 10
class HwsConfig(utils.ConfigUtil):
    def __init__(self):
        self.local_vpn_thread = None
        self.cloud_vpn_thread = None
        self.cascading_thread = None
        self.cascaded_thread = None

        self.install_info = None
        self.proxy_info = None
        self.installer = None
        self.cloud_info = None
        self.cloud_params = None

    def initialize(self, cloud_params, install_info, proxy_info, cloud_info, installer):
        self.cloud_params = cloud_params
        self.install_info = install_info
        self.proxy_info = proxy_info
        self.installer = installer
        self.cloud_info = cloud_info
        pdb.set_trace()
        if proxy_info:
            self.installer.cloud_info_handler.write_proxy(proxy_info)

    def config_vpn_only(self):
        LOG.info("config cloud vpn only")
        pass

    def _config_cascading_vpn(self):
        LOG.info("config local vpn")
        vpn_conn_name = self.install_info["vpn_conn_name"]
        local_vpn_cf = VpnConfiger(
                host_ip=self.install_info['cascading_vpn_info']['external_api_ip'],
                user=constant.VpnConstant.VPN_ROOT,
                password=constant.VpnConstant.VPN_ROOT_PWD)

        local_vpn_cf.register_add_conns(
                tunnel_name=vpn_conn_name["api_conn_name"],
                left_public_ip=self.install_info['cascading_vpn_info']['public_ip'],
                left_subnet=self.install_info['cascading_subnets_info']['external_api'],
                right_public_ip=self.install_info["cascaded_vpn_info"]["public_ip"],
                right_subnet=self.install_info["cascaded_subnets_info"]["external_api"])

        local_vpn_cf.register_add_conns(
                tunnel_name=vpn_conn_name["tunnel_conn_name"],
                left_public_ip=self.install_info['cascading_vpn_info']['public_ip'],
                left_subnet=self.install_info['cascading_subnets_info']['tunnel_bearing'],
                right_public_ip=self.install_info['cascaded_vpn_info']['public_ip'],
                right_subnet=self.install_info['cascaded_subnets_info']['tunnel_bearing'])
        local_vpn_cf.do_config()

    def _config_cascaded_vpn(self):
        LOG.info("config vcloud vpn thread")
        vpn_conn_name = self.install_info["vpn_conn_name"]
        cloud_vpn_cf = VpnConfiger(
                host_ip=self.install_info["cascaded_vpn_info"]["public_ip"],
                user=constant.VpnConstant.VCLOUD_VPN_ROOT,
                password=constant.VpnConstant.VCLOUD_VPN_ROOT_PWD)

        cloud_vpn_cf.register_add_conns(
                tunnel_name=vpn_conn_name["api_conn_name"],
                left_public_ip=self.install_info['cascaded_vpn_info']['public_ip'],
                left_subnet=self.install_info["cascaded_subnets_info"]["external_api"],
                right_public_ip=self.install_info['cascading_vpn_info']['public_ip'],
                right_subnet=self.install_info['cascading_subnets_info']['external_api'])

        cloud_vpn_cf.register_add_conns(
                tunnel_name=vpn_conn_name["tunnel_conn_name"],
                left_public_ip=self.install_info['cascaded_vpn_info']['public_ip'],
                left_subnet=self.install_info['cascaded_subnets_info']['tunnel_bearing'],
                right_public_ip=self.install_info['cascading_vpn_info']['public_ip'],
                right_subnet=self.install_info['cascading_subnets_info']['tunnel_bearing'])
        cloud_vpn_cf.do_config()

    def config_vpn(self):
        self._config_cascading_vpn()
        self._config_cascaded_vpn()
        pass

    def _config_cascading_route(self):
        LOG.info("add route to cascading ...")
        self._add_vpn_route_with_api(
                host_ip=self.install_info['cascading_info']['external_api_ip'],
                user=constant.Cascading.ROOT,
                passwd=constant.Cascading.ROOT_PWD,
                access_cloud_api_subnet=
                self.install_info["cascaded_subnets_info"]["external_api"],
                api_gw=self.install_info["cascading_vpn_info"]['external_api_ip'],
                access_cloud_tunnel_subnet=
                self.install_info["cascaded_subnets_info"]["tunnel_bearing"],
                tunnel_gw=self.install_info["cascading_vpn_info"]['tunnel_bearing_ip'])

    @RetryDecorator(max_retry_count=MAX_RETRY,
                raise_exception=InstallCascadedFailed(
                    current_step="_config_cascaded_route"))
    def _config_cascaded_route(self):
        LOG.info("add route to hws on cascaded ...")
        check_host_status(
                host=self.install_info["cascaded_info"]["public_ip"],
                user=constant.HwsConstant.ROOT,
                password=constant.HwsConstant.ROOT_PWD,
                retry_time=100, interval=3)    #wait cascaded vm started

        self._add_vpn_route_with_api(
                host_ip=self.install_info["cascaded_info"]["public_ip"],
                user=constant.HwsConstant.ROOT,
                passwd=constant.HwsConstant.ROOT_PWD,
                access_cloud_api_subnet=
                self.install_info["cascading_subnets_info"]["external_api"],
                api_gw=self.install_info["cascaded_vpn_info"]["external_api_ip"],
                access_cloud_tunnel_subnet=
                self.install_info["cascading_subnets_info"]["tunnel_bearing"],
                tunnel_gw=self.install_info["cascaded_vpn_info"]["tunnel_bearing_ip"])

        check_host_status(
                    host=self.install_info["cascaded_info"]["external_api_ip"],
                    user=constant.HwsConstant.ROOT,
                    password=constant.HwsConstant.ROOT_PWD,
                    retry_time=1, interval=1)    #test api net

    def config_route(self):
        self._config_cascading_route()
        self._config_cascaded_route()
        pass

    @staticmethod
    def _add_vpn_route_with_api(host_ip, user, passwd,
                       access_cloud_api_subnet, api_gw,
                       access_cloud_tunnel_subnet, tunnel_gw):
        try:
            execute_cmd_without_stdout(
                host=host_ip,
                user=user,
                password=passwd,
                cmd='cd %(dir)s; sh %(script)s '
                    '%(access_cloud_api_subnet)s %(api_gw)s %(access_cloud_tunnel_subnet)s %(tunnel_gw)s'
                    % {"dir": constant.VpnConstant.REMOTE_ROUTE_SCRIPTS_DIR,
                       "script": constant.VpnConstant.ADD_VPN_ROUTE_SCRIPT,
                       "access_cloud_api_subnet":access_cloud_api_subnet,
                       "api_gw":api_gw,
                       "access_cloud_tunnel_subnet": access_cloud_tunnel_subnet,
                       "tunnel_gw": tunnel_gw})
        except exception.SSHCommandFailure:
            LOG.error("add vpn route error, host: %s" % host_ip)
            return False
        return True

    @staticmethod
    def _add_vpn_route(host_ip, user, passwd,
                       access_cloud_tunnel_subnet, tunnel_gw):
        try:
            execute_cmd_without_stdout(
                host=host_ip,
                user=user,
                password=passwd,
                cmd='cd %(dir)s; sh %(script)s '
                    '%(access_cloud_tunnel_subnet)s %(tunnel_gw)s'
                    % {"dir": constant.VpnConstant.REMOTE_ROUTE_SCRIPTS_DIR,
                       "script": constant.VpnConstant.ADD_VPN_ROUTE_SCRIPT,
                       "access_cloud_tunnel_subnet": access_cloud_tunnel_subnet,
                       "tunnel_gw": tunnel_gw})
        except exception.SSHCommandFailure:
            LOG.error("add vpn route error, host: %s" % host_ip)
            return False
        return True

    def config_cascading(self):
        #TODO(lrx):remove v2v_gw
        LOG.info("config cascading")

        cascading_cf = CascadingConfiger(
                cascading_ip=self.install_info["cascading_info"]["external_api_ip"],
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cascaded_domain=self.install_info["cascaded_info"]["domain"],
                cascaded_api_ip=self.install_info["cascaded_info"]["external_api_ip"],
                v2v_gw='1.1.1.1')
        cascading_cf.do_config()

    def config_cascaded(self):
        LOG.info("config cascaded")

        cascaded_cf = CascadedConfiger(
                public_ip_api = self.install_info["cascaded_info"]["public_ip"],
                api_ip = self.install_info["cascaded_info"]["external_api_ip"],
                domain = self.install_info["cascaded_info"]['domain'],
                user = constant.HwsConstant.ROOT,
                password = constant.HwsConstant.ROOT_PWD,
                cascading_domain = self.install_info['cascading_info']['domain'],
                cascading_api_ip = self.install_info["cascading_info"]["external_api_ip"],
                cascaded_api_subnet_gateway=
                self.install_info['cascaded_subnets_info']['external_api_gateway_ip'])

        cascaded_cf.do_config()

    def config_proxy(self):
        # config proxy on cascading host
        pdb.set_trace()
        LOG.info("config proxy ...")
        if self.proxy_info is None:
            LOG.info("wait proxy ...")
            self.proxy_info = self._get_proxy_retry()

        LOG.info("add dhcp to proxy ...")

        proxy_id = self.proxy_info["id"]
        proxy_num = self.proxy_info["proxy_num"]
        LOG.debug("proxy_id = %s, proxy_num = %s"
                     % (proxy_id, proxy_num))

        self._config_proxy(
                self.install_info['cascading_info']['external_api_ip'],
                self.proxy_info)

        pass

    @staticmethod
    def _config_proxy(cascading_ip, proxy_info):
        LOG.info("command role host add...")
        for i in range(3):
            try:
                execute_cmd_without_stdout(
                    host=cascading_ip,
                    user=constant.Cascading.ROOT,
                    password=constant.Cascading.ROOT_PWD,
                    cmd="cps role-host-add --host %(proxy_host_name)s dhcp;"
                        "cps commit"
                        % {"proxy_host_name": proxy_info["id"]})
            except exception.SSHCommandFailure:
                LOG.error("config proxy error, try again...")
        return True

    def _get_proxy_retry(self):
        LOG.info("get proxy retry ...")
        proxy_info = proxy_manager.distribute_proxy(self.installer)
        for i in range(10):
            if proxy_info is None:
                time.sleep(240)
                proxy_info = proxy_manager.distribute_proxy(self.installer)
            else:
                return proxy_info
        raise exception.ConfigProxyFailure(error="check proxy config result failed")

    def config_patch(self):
        LOG.info("config patches config ...")
        pdb.set_trace()

        cascaded_public_ip = self.install_info["cascaded_info"]['tunnel_bearing_ip']

        self._config_patch_tools(
                host_ip=self.install_info['cascading_info']['external_api_ip'],
                user=constant.Cascading.ROOT,
                passwd=constant.Cascading.ROOT_PWD,
                cascaded_domain=self.install_info['cascaded_info']['domain'],
                proxy_info=self.proxy_info,
                install_info=self.install_info)

        self._config_hws(
                host_ip=cascaded_public_ip,
                user=constant.HwsConstant.ROOT,
                passwd=constant.HwsConstant.ROOT_PWD)

        self._deploy_patches(self.install_info['cascading_info']['external_api_ip'],
                             user=constant.Cascading.ROOT,
                             passwd=constant.Cascading.ROOT_PWD)

        self._start_hws_gateway(self.install_info["cascaded_info"]["public_ip"],
                                constant.HwsConstant.ROOT,
                                constant.HwsConstant.ROOT_PWD)

    def _config_patch_tools(self, host_ip, user, passwd,
                            cascaded_domain, proxy_info, install_info):
        LOG.info("config patches tools  ...")
        for i in range(10):
            try:
                pdb.set_trace()
                execute_cmd_without_stdout(
                    host=host_ip, user=user, password=passwd,
                     cmd='cd %(dis)s; sh %(script)s '
                        '%(proxy_num)s %(proxy_host_name)s %(cascaded_domain)s '
                        '%(local_api_subnet)s %(cloud_vpn_api_ip)s '
                        '%(local_tunnel_subnet)s %(cloud_vpn_tunnel_ip)s '
                        '%(cascading_domain)s'
                        % {"dis": constant.PatchesConstant.REMOTE_SCRIPTS_DIR,
                           "script":
                               constant.PatchesConstant.CONFIG_PATCHES_SCRIPT,
                           "proxy_num": proxy_info["proxy_num"],
                           "proxy_host_name": proxy_info["id"],
                           "cascaded_domain": cascaded_domain,
                           "local_api_subnet": install_info['cascading_subnets_info']['external_api'],
                           "cloud_vpn_api_ip": install_info["cascaded_vpn_info"]["external_api_ip"],
                           "local_tunnel_subnet": install_info['cascading_subnets_info']['tunnel_bearing'],
                           "cloud_vpn_tunnel_ip": install_info["cascaded_vpn_info"]["tunnel_bearing_ip"],
                           "cascading_domain": install_info["cascading_info"]["domain"]})
                return True
            except Exception as e:
                LOG.error("config patch tool error, error: %s"
                             % e.message)
                continue
        return True

    def _config_hws(self,host_ip, user, passwd):
        LOG.info("config hws /etc/nova/nova.json ...")
        pdb.set_trace()
        for i in range(5):
            try:
                gong_yao = self.cloud_params['ak']
                si_yao = self.cloud_params['sk']
                region = self.cloud_params['region']
                host = self.cloud_params['host']
                project_id = self.cloud_params['project_id']
                resource_region = self.cloud_params['availability_zone']
                host_endpoint = ".".join([region, host, 'com.cn' ])
                ecs_host = 'ecs.' + host_endpoint
                evs_host = 'evs.' + host_endpoint
                ims_host = 'ims.' + host_endpoint
                vpc_host = 'vpc.' + host_endpoint
                vpc_id = self.install_info["cascaded_subnets_info"]["vpc_id"]
                tunnel_bearing_id = self.install_info["cascaded_subnets_info"]["tunnel_bearing_id"]
                internal_base_id = self.install_info["cascaded_subnets_info"]["internal_base_id"]
                subnet_id = tunnel_bearing_id + "," + internal_base_id
                execute_cmd_without_stdout(
                    host=host_ip, user=user, password=passwd,
                    cmd='cd %(dis)s; sh %(script)s '
                        '%(project_id)s %(vpc_id)s %(subnet_id)s '
                        '%(service_region)s %(resource_region)s '
                        '%(ecs_host)s %(ims_host)s '
                        '%(evs_host)s %(vpc_host)s '
                        '%(gong_yao)s %(si_yao)s '
                        '%(tunnel_cidr)s %(route_gw)s '
                        % {"dis": constant.PatchesConstant.REMOTE_HWS_SCRIPTS_DIR,
                           "script":
                               constant.PatchesConstant.CONFIG_HWS_SCRIPT,
                           "project_id": project_id,
                           "vpc_id": vpc_id,
                           "subnet_id": subnet_id,
                           "service_region": region,
                           "resource_region": resource_region,
                           "ecs_host": ecs_host,
                           "ims_host": ims_host,
                           "evs_host": evs_host,
                           "vpc_host": vpc_host,
                           "gong_yao": gong_yao,
                           "si_yao": si_yao,
                           "tunnel_cidr":
                               self.install_info["cascaded_subnets_info"]["tunnel_bearing"],
                           "route_gw":
                               self.install_info["cascaded_vpn_info"]["tunnel_bearing_ip"]
                            })
                return True
            except Exception as e:
                LOG.error("config hws error, error: %s"
                             % e.message)
                continue
        return True


    @staticmethod
    def _deploy_patches(host_ip, user, passwd):
        LOG.info("deploy patches ...")
        pdb.set_trace()
        execute_cmd_without_stdout(
            host=host_ip, user=user, password=passwd,
            cmd='cd %s; python config.py cascading'
                % constant.PatchesConstant.PATCH_LUNCH_DIR)
        return True
    
    @staticmethod
    def _start_hws_gateway(host_ip, user, passwd):
        LOG.info("start hws java gateway ...")
        pdb.set_trace()
        execute_cmd_without_stdout(
                    host=host_ip, user=user, password=passwd,
                    cmd='cd %(dis)s; sh %(script)s '
                    % {"dis": constant.PatchesConstant.REMOTE_HWS_SCRIPTS_DIR,
                        "script":
                        constant.PatchesConstant.START_HWS_GATEWAY_SCRIPT}
                    )

    def config_storge(self):
        LOG.info("config storage...")
        #pdb.set_trace()

        self._config_storage(
                host= self.install_info['cascaded_info']['external_api_ip'],
                user=constant.HwsConstant.ROOT,
                password=constant.HwsConstant.ROOT_PWD,
                cascading_domain=self.install_info['cascading_info']['domain'],
                cascaded_domain=self.install_info['cascaded_info']['domain'],
                )

    def _config_storage(self, host, user, password, cascading_domain,
                        cascaded_domain):
        # 1. create env file and config cinder on cascaded host
        for i in range(7):
            try:
                execute_cmd_without_stdout(
                    host=host, user=user, password=password,
                    cmd='cd %(dir)s;'
                        'sh %(create_env_script)s %(cascading_domain)s '
                        '%(cascaded_domain)s;'
                        % {"dir": constant.Cascaded.REMOTE_HWS_SCRIPTS_DIR,
                           "create_env_script": constant.Cascaded.CREATE_ENV,
                           "cascading_domain": cascading_domain,
                           "cascaded_domain": cascaded_domain,
                           })
                break
            except Exception as e1:
                LOG.error("modify env file and config cinder "
                             "on cascaded host error: %s"
                             % e1.message)
                time.sleep(1)
                continue

        return True

    def remove_existed_cloud(self):
        #config cascading unregister
        cascading_api_ip = self.install_info["cascading_info"]["external_api_ip"]
        try:
            execute_cmd_without_stdout(
                host= cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_CINDER_SERVICE_SCRIPT,
                       "cascaded_domain": self.install_info["cascaded_info"]["domain"]})
        except Exception as e:
            LOG.error("remove cinder service error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(
                host= cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
                       "cascaded_domain": self.install_info["cascaded_info"]["domain"]})

            execute_cmd_without_stdout(
                host= cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(proxy_host)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
                       "proxy_host": self.install_info["proxy_info"]["id"]})

        except Exception as e:
            LOG.error("remove neutron agent error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(
                host= cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.RemoveConstant.REMOVE_KEYSTONE_SCRIPT,
                       "cascaded_domain": self.install_info["cascaded_info"]["domain"]})
        except SSHCommandFailure:
            LOG.error("remove keystone endpoint error.")

        try:
            execute_cmd_without_stdout(
                host= cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; '
                    'sh %(script)s %(proxy_host_name)s %(proxy_num)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.RemoveConstant.REMOVE_PROXY_SCRIPT,
                       "proxy_host_name": self.install_info["proxy_info"]["id"],
                       "proxy_num": self.install_info["proxy_info"]["proxy_num"]})
        except SSHCommandFailure:
            LOG.error("remove proxy error.")


        cascaded_api_ip = self.install_info["cascaded_info"]['external_api_ip']

        address = "/%(cascaded_domain)s/%(cascaded_ip)s" \
                  % {"cascaded_domain": self.install_info["cascaded_info"]["domain"],
                     "cascaded_ip": cascaded_api_ip}

        try:
            execute_cmd_without_stdout(
                host= cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s remove %(address)s'
                    % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.PublicConstant.MODIFY_DNS_SERVER_ADDRESS,
                       "address": address})
        except SSHCommandFailure:
            LOG.error("remove dns address error.")

        try:
            execute_cmd_without_stdout(
                host= cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='ip route del %(tunnel_route)s; ip route del %(api_route)s;'
                    % {"tunnel_route":
                           self.install_info["cascaded_subnets_info"]["tunnel_bearing"],
                       "api_route":
                           self.install_info["cascaded_subnets_info"]["external_api"]})
        except SSHCommandFailure:
            LOG.error("remove cascaded route error.")

        # config local_vpn
        vpn_conn_name = self.install_info["vpn_conn_name"]
        try:
            local_vpn = VPN(self.install_info["cascading_vpn_info"]["external_api_ip"],
                            constant.VpnConstant.VPN_ROOT,
                            constant.VpnConstant.VPN_ROOT_PWD)
            local_vpn.remove_tunnel(vpn_conn_name["api_conn_name"])
            local_vpn.remove_tunnel(vpn_conn_name["tunnel_conn_name"])
        except SSHCommandFailure:
            LOG.error("remove conn error.")



