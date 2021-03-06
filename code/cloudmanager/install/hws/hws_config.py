

from heat.openstack.common import log as logging
from heat.engine.resources.cloudmanager.vpn_configer import VpnConfiger
from heat.engine.resources.cloudmanager.vpn import VPN
import heat.engine.resources.cloudmanager.constant as constant
#import threading
import time
import heat.engine.resources.cloudmanager.proxy_manager as proxy_manager
from heat.engine.resources.cloudmanager.cascading_configer import CascadingConfiger
from hws_cascaded_configer import CascadedConfiger
from heat.engine.resources.cloudmanager.commonutils import *
import heat.engine.resources.cloudmanager.exception as exception
from heat.engine.resources.cloudmanager.exception import *
from heat.engine.resources.cloudmanager.util.retry_decorator import RetryDecorator
from hws_cloud_info_persist import *
from hws_util import *
import heat.engine.resources.cloudmanager.util.conf_util as conf_util

LOG = logging.getLogger(__name__)
MAX_RETRY = 10
class HwsConfig(object):
    def __init__(self):
        self.install_info = None
        self.proxy_info = None
        self.cloud_params = None
        self.cloud_info_handler = None

    def initialize(self, cloud_params, install_info):
        self.cloud_params = cloud_params

        default_params = conf_util.read_conf(constant.Cascading.HWS_CONF_FILE)
        self.cloud_params["project_info"]["host"]= default_params["project_info"]["host"]

        self.install_info = install_info
        self.proxy_info = self.install_info["proxy_info"]
        cloud_id = self.install_info["cloud_id"]
        self.cloud_info_handler = \
            HwsCloudInfoPersist(constant.HwsConstant.CLOUD_INFO_FILE, cloud_id)
        self._modify_cascaded_external_api()

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
                user=constant.VpnConstant.VPN_ROOT,
                password=constant.VpnConstant.VPN_ROOT_PWD)

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

    def _enable_network_cross(self):
        cloud_id = self.install_info["cloud_id"]

        vpn_cfg = VpnConfiger(
                host_ip=self.install_info["cascaded_vpn_info"]["public_ip"],
                user=constant.VpnConstant.VPN_ROOT,
                password=constant.VpnConstant.VPN_ROOT_PWD)

        for other_cloud_id in self.cloud_info_handler.list_all_cloud_id():
            if other_cloud_id == cloud_id:
                continue

            other_cloud = \
                self.cloud_info_handler.get_cloud_info_with_id(other_cloud_id)
            if not other_cloud["access"]:
                continue

            other_vpn_cfg = VpnConfiger(host_ip=other_cloud["cascaded_vpn_info"]["public_ip"],
                            user=constant.VpnConstant.VPN_ROOT,
                            password=constant.VpnConstant.VPN_ROOT_PWD)

            LOG.info("add conn on tunnel vpns...")
            tunnel_conn_name = "%s-tunnel-%s" % (cloud_id, other_cloud_id)
            vpn_cfg.register_add_conns(
                tunnel_name=tunnel_conn_name,
                left_public_ip=self.install_info["cascaded_vpn_info"]["public_ip"],
                left_subnet=self.install_info["cascaded_subnets_info"]["tunnel_bearing"],
                right_public_ip=other_cloud["cascaded_vpn_info"]["public_ip"],
                right_subnet=other_cloud["cascaded_subnets_info"]["tunnel_bearing"])

            other_vpn_cfg.register_add_conns(
                tunnel_name=tunnel_conn_name,
                left_public_ip=other_cloud["cascaded_vpn_info"]["public_ip"],
                left_subnet=other_cloud["cascaded_subnets_info"]["tunnel_bearing"],
                right_public_ip=self.install_info['cascaded_vpn_info']['public_ip'],
                right_subnet=self.install_info['cascaded_subnets_info']['tunnel_bearing'])
            vpn_cfg.do_config()
            other_vpn_cfg.do_config()

            LOG.info("add route on cascadeds...")
            execute_cmd_without_stdout(
                host=self.install_info["cascaded_info"]["public_ip"],
                user=constant.HwsConstant.ROOT,
                password=constant.HwsConstant.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
                    % {"dir": constant.Cascaded.REMOTE_HWS_SCRIPTS_DIR,
                       "script": constant.Cascaded.ADD_API_ROUTE_SCRIPT,
                       "subnet": other_cloud["cascaded_subnets_info"]["tunnel_bearing"],
                       "gw": self.install_info["cascaded_vpn_info"]['tunnel_bearing_ip']})

            execute_cmd_without_stdout(
                host=self.install_info["cascaded_info"]["public_ip"],
                user=constant.HwsConstant.ROOT,
                password=constant.HwsConstant.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s '
                    '%(access_cloud_tunnel_subnet)s %(tunnel_gw)s '
                    '%(cloud_id)s'
                    % {"dir": constant.AfterRebootConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.AfterRebootConstant.ADD_ROUTE_SCRIPT,
                       "access_cloud_tunnel_subnet": other_cloud["cascaded_subnets_info"]["tunnel_bearing"],
                       "tunnel_gw": self.install_info["cascaded_vpn_info"]['tunnel_bearing_ip'],
                       "cloud_id": other_cloud_id})

            execute_cmd_without_stdout(
                host=other_cloud["cascaded_info"]["public_ip"],
                user=constant.HwsConstant.ROOT,
                password=constant.HwsConstant.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
                    % {"dir": constant.Cascaded.REMOTE_HWS_SCRIPTS_DIR,
                       "script": constant.Cascaded.ADD_API_ROUTE_SCRIPT,
                       "subnet": self.install_info["cascaded_subnets_info"]["tunnel_bearing"],
                       "gw": other_cloud["cascaded_vpn_info"]['tunnel_bearing_ip']})

            execute_cmd_without_stdout(
                host=other_cloud["cascaded_info"]["public_ip"],
                user=constant.HwsConstant.ROOT,
                password=constant.HwsConstant.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s '
                    '%(access_cloud_tunnel_subnet)s %(tunnel_gw)s '
                    '%(cloud_id)s'
                    % {"dir": constant.AfterRebootConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.AfterRebootConstant.ADD_ROUTE_SCRIPT,
                       "access_cloud_tunnel_subnet": self.install_info["cascaded_subnets_info"]["tunnel_bearing"],
                       "tunnel_gw": other_cloud["cascaded_vpn_info"]['tunnel_bearing_ip'],
                       "cloud_id": cloud_id})

            # add cloud-sg
            LOG.info("add security group...")
            #TODO
        return True

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
                tunnel_gw=self.install_info["cascading_vpn_info"]['tunnel_bearing_ip'],
                cloud_id=self.cloud_params["azname"])

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

        """
        execute_cmd_without_stdout(
                host=self.install_info["cascaded_info"]["public_ip"],
                user=constant.HwsConstant.ROOT,
                password=constant.HwsConstant.ROOT_PWD,
                cmd="source /root/adminrc/; cps network-update --name tunnel_bearing --subnet %(tunnel_bearing_cidr)s"
                    % {"tunnel_bearing_cidr":self.install_info["cascaded_subnets_info"]["tunnel_bearing"]},
                retry_time=10, interval=3)    
        """
        self._add_vpn_route_with_api(
                host_ip=self.install_info["cascaded_info"]["public_ip"],
                user=constant.HwsConstant.ROOT,
                passwd=constant.HwsConstant.ROOT_PWD,
                access_cloud_api_subnet=
                self.install_info["cascading_subnets_info"]["external_api"],
                api_gw=self.install_info["cascaded_vpn_info"]["external_api_ip"],
                access_cloud_tunnel_subnet=
                self.install_info["cascading_subnets_info"]["tunnel_bearing"],
                tunnel_gw=self.install_info["cascaded_vpn_info"]["tunnel_bearing_ip"],
                cloud_id="cascading"
        )

        check_host_status(
                    host=self.install_info["cascaded_info"]["external_api_ip"],
                    user=constant.HwsConstant.ROOT,
                    password=constant.HwsConstant.ROOT_PWD,
                    retry_time=100, interval=3)    #test api net

    def _modify_cascaded_external_api(self):
        #ssh to vpn, then ssh to cascaded through vpn tunnel_bearing_ip
        modify_cascaded_api_domain_cmd = 'cd %(dir)s; ' \
                    'source /root/adminrc; ' \
                    'python %(script)s '\
                    '%(cascading_domain)s %(cascading_api_ip)s '\
                    '%(cascaded_domain)s %(cascaded_ip)s '\
                    '%(gateway)s'\
                    % {"dir": constant.Cascaded.REMOTE_HWS_SCRIPTS_DIR,
                       "script":constant.Cascaded.MODIFY_CASCADED_SCRIPT_PY,
                       "cascading_domain": self.install_info['cascading_info']['domain'],
                       "cascading_api_ip": self.install_info["cascading_info"]["external_api_ip"],
                       "cascaded_domain": self.install_info["cascaded_info"]['domain'],
                       "cascaded_ip": self.install_info["cascaded_info"]["external_api_ip"],
                       "gateway": self.install_info['cascaded_subnets_info']['external_api_gateway_ip']}
        #pdb.set_trace()
        for i in range(100):
            try:
                execute_cmd_without_stdout(
                    host= self.install_info["cascaded_vpn_info"]["public_ip"],
                    user=constant.VpnConstant.VPN_ROOT,
                    password=constant.VpnConstant.VPN_ROOT_PWD,
                    cmd='cd %(dir)s; python %(script)s '
                        '%(cascaded_tunnel_ip)s %(user)s %(passwd)s \'%(cmd)s\''
                    % {"dir": constant.VpnConstant.REMOTE_ROUTE_SCRIPTS_DIR,
                       "script": constant.VpnConstant.MODIFY_CASCADED_API_SCRIPT,
                       "cascaded_tunnel_ip": self.install_info["cascaded_info"]["tunnel_bearing_ip"],
                       "user": constant.HwsConstant.ROOT,
                       "passwd": constant.HwsConstant.ROOT_PWD,
                       "cmd": modify_cascaded_api_domain_cmd})
                return True
            except Exception:
                #wait cascaded vm to reboot ok
                time.sleep(10)
                continue
        LOG.error("modify cascaded=%s external_api ip and domain error"
                  % self.install_info["cascaded_info"]["tunnel_bearing_ip"])

    def config_route(self):
        self._config_cascading_route()
        self._config_cascaded_route()





    @staticmethod
    def _add_vpn_route_with_api(host_ip, user, passwd,
                       access_cloud_api_subnet, api_gw,
                       access_cloud_tunnel_subnet, tunnel_gw, cloud_id):
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

            execute_cmd_without_stdout(
                host=host_ip,
                user=user,
                password=passwd,
                cmd='cd %(dir)s; sh %(script)s '
                    '%(access_cloud_api_subnet)s %(api_gw)s '
                    '%(access_cloud_tunnel_subnet)s %(tunnel_gw)s '
                    '%(cloud_id)s'
                    % {"dir": constant.AfterRebootConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.AfterRebootConstant.ADD_ROUTE_SCRIPT,
                       "access_cloud_api_subnet":access_cloud_api_subnet,
                       "api_gw":api_gw,
                       "access_cloud_tunnel_subnet": access_cloud_tunnel_subnet,
                       "tunnel_gw": tunnel_gw,
                       "cloud_id": cloud_id})

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
                cascaded_domain = self.install_info['cascaded_info']['domain'],
                cascaded_api_ip = self.install_info["cascaded_info"]["external_api_ip"],
                cascaded_api_subnet_gateway=
                self.install_info['cascaded_subnets_info']['external_api_gateway_ip']
        )

        cascaded_cf.do_config()

    def config_proxy(self):
        # config proxy on cascading host
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
        proxy_info = proxy_manager.distribute_proxy()
        for i in range(10):
            if proxy_info is None:
                time.sleep(240)
                proxy_info = proxy_manager.distribute_proxy()
            else:
                return proxy_info
        raise exception.ConfigProxyFailure(error="check proxy config result failed")

    def config_patch(self):
        LOG.info("config patches config ...")

        cascaded_public_ip = self.install_info["cascaded_info"]['public_ip']

        self._config_patch_tools(
                host_ip=self.install_info['cascading_info']['external_api_ip'],
                user=constant.Cascading.ROOT,
                passwd=constant.Cascading.ROOT_PWD,
                cascaded_domain=self.install_info['cascaded_info']['domain'],
                proxy_info=self.proxy_info,
                install_info=self.install_info)

        self._deploy_patches(self.install_info['cascading_info']['external_api_ip'],
                             user=constant.Cascading.ROOT,
                             passwd=constant.Cascading.ROOT_PWD)

        self._config_hws(
                host_ip=cascaded_public_ip,
                user=constant.HwsConstant.ROOT,
                passwd=constant.HwsConstant.ROOT_PWD)

        start_hws_gateway(self.install_info["cascaded_info"]["public_ip"],
                                constant.HwsConstant.ROOT,
                                constant.HwsConstant.ROOT_PWD)

    def _config_patch_tools(self, host_ip, user, passwd,
                            cascaded_domain, proxy_info, install_info):
        LOG.info("config patches tools  ...")
        for i in range(10):
            try:
                execute_cmd_without_stdout(
                    host=host_ip, user=user, password=passwd,
                     cmd='cd %(dis)s; sh %(script)s '
                        '%(proxy_num)s %(proxy_host_name)s %(cascaded_domain)s '
                        '%(cascading_domain)s'
                        % {"dis": constant.PatchesConstant.REMOTE_SCRIPTS_DIR,
                           "script":
                               constant.PatchesConstant.CONFIG_PATCHES_SCRIPT,
                           "proxy_num": proxy_info["proxy_num"],
                           "proxy_host_name": proxy_info["id"],
                           "cascaded_domain": cascaded_domain,
                            "cascading_domain": install_info["cascading_info"]["domain"]})
                return True
            except Exception as e:
                LOG.error("config patch tool error, error: %s"
                             % e.message)
                continue
        return True

    def _config_hws(self,host_ip, user, passwd):
        LOG.info("config hws /etc/nova/nova.json ...")
        project_info = self.cloud_params["project_info"]
        for i in range(5):
            try:
                gong_yao = project_info['access_key']
                si_yao = project_info['secret_key']
                region = project_info['region']
                host = project_info['host']
                project_id = project_info['project_id']
                resource_region = project_info['availability_zone']
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
                        '%(rabbit_host_ip)s %(security_group_vpc)s'
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
                               self.install_info["cascaded_vpn_info"]["tunnel_bearing_ip"],
                           "rabbit_host_ip":self.install_info["cascaded_info"]["internal_base_ip"],
                           "security_group_vpc":self.install_info["cascaded_subnets_info"]["security_group_id"]
                            })

                self._restart_nova_computer(host_ip, user, passwd)
                return True
            except Exception as e:
                LOG.error("config hws error, error: %s"
                             % e.message)
                continue

        return True
    @staticmethod
    def _restart_nova_computer(host_ip, user, passwd):
        execute_cmd_without_stdout(
            host=host_ip, user=user, password=passwd,
            cmd='source /root/adminrc;'
                'cps host-template-instance-operate --action stop --service nova nova-compute')
        time.sleep(1)
        execute_cmd_without_stdout(
            host=host_ip, user=user, password=passwd,
            cmd='source /root/adminrc;'
                'cps host-template-instance-operate --action start --service nova nova-compute')

    @staticmethod
    def _deploy_patches(host_ip, user, passwd):
        LOG.info("deploy patches ...")
        try:
            execute_cmd_without_stdout(
                host=host_ip, user=user, password=passwd,
                cmd='cd %s; python config.py cascading'
                    % constant.PatchesConstant.PATCH_LUNCH_DIR)
        except exception.SSHCommandFailure as e:
                LOG.error("config.py cascading error: %s"
                             % (e.format_message()))
        return True


    def config_storge(self):
        LOG.info("config storage...")
        #pdb.set_trace()

        self._config_storage(
                host= self.install_info['cascaded_info']['public_ip'],
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

    def config_extnet(self):
        self._config_extnet()

    def _config_extnet(self):
        self._enable_network_cross()

    def remove_existed_cloud(self):
        if self.install_info is None:
            return
        self.remove_aggregate()
        self.remove_cinder()
        self.remove_neutron_agent()
        self.remove_keystone()
        self.remove_proxy()
        self.remove_dns()
        self.remove_route()
        self.remove_vpn_tunnel()
        stop_hws_gateway(host_ip= self.install_info["cascading_info"]["external_api_ip"],
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD)

    def remove_aggregate(self):
        cascading_api_ip = self.install_info["cascading_info"]["external_api_ip"]
        try:
            execute_cmd_without_stdout(
                host=cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_AGGREGATE_SCRIPT,
                       "cascaded_domain": self.install_info["cascaded_info"]["domain"]})
        except Exception as e:
            LOG.error("remove aggregate error, error: %s" % e.message)

    def remove_cinder(self):
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

    def remove_neutron_agent(self):
        cascading_api_ip = self.install_info["cascading_info"]["external_api_ip"]
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

    def remove_keystone(self):
        cascading_api_ip = self.install_info["cascading_info"]["external_api_ip"]
        try:
            execute_cmd_without_stdout(
                host= cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.RemoveConstant.REMOVE_KEYSTONE_SCRIPT,
                       "cascaded_domain": self.install_info["cascaded_info"]["domain"]})
        except Exception as e:
            LOG.error("remove keystone endpoint error: %s" % e.message)

    def remove_proxy(self):
        cascading_api_ip = self.install_info["cascading_info"]["external_api_ip"]
        if self.install_info["proxy_info"] is None:
            LOG.info("proxy is None")
            return
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
        except Exception as e:
            LOG.error("remove proxy error: %s" % e.message)

    def remove_dns(self):
        cascading_api_ip = self.install_info["cascading_info"]["external_api_ip"]
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

    def disable_cross_network(self):
        cloud_id = self.install_info["cloud_id"]
        for other_cloud_id in self.cloud_info_handler.list_all_cloud_id():
            if other_cloud_id == cloud_id:
                continue

            other_cloud = \
                self.cloud_info_handler.get_cloud_info_with_id(other_cloud_id)
            if not other_cloud["access"]:
                continue

            other_vpn_cfg = VpnConfiger(host_ip=other_cloud["cascaded_vpn_info"]["public_ip"],
                            user=constant.VpnConstant.VPN_ROOT,
                            password=constant.VpnConstant.VPN_ROOT_PWD)

            LOG.info("remove conn on tunnel vpns...")
            tunnel_conn_name = "%s-tunnel-%s" % (cloud_id, other_cloud_id)

            other_vpn_cfg.register_remove_conns(conn_name=tunnel_conn_name)
            other_vpn_cfg.do_config()

            LOG.info("remove route on cascadeds...")
            execute_cmd_without_stdout(
                host=other_cloud["cascaded_info"]["public_ip"],
                user=constant.HwsConstant.ROOT,
                password=constant.HwsConstant.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(subnet)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.RemoveConstant.REMOVE_ROUTE_SCRIPT,
                       "subnet": self.install_info["cascaded_subnets_info"]["tunnel_bearing"]
                       })

            add_route_file = "add_vpn_route_" + self.install_info["azname"] + ".sh"
            execute_cmd_without_stdout(
                host=other_cloud["cascaded_info"]["public_ip"],
                user=constant.HwsConstant.ROOT,
                password=constant.HwsConstant.ROOT_PWD,
                cmd='cd %(dir)s; rm %(script)s '
                    % {"dir": constant.AfterRebootConstant.REMOTE_ROUTE_SCRIPTS_DIR,
                       "script": add_route_file})

            # del cloud-sg
            LOG.info("del security group...")
            #TODO
        return True
        pass

    def remove_route(self):
        cascading_api_ip = self.install_info["cascading_info"]["external_api_ip"]
        try:
            execute_cmd_without_stdout(
                host= cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; rm -f %(script_after_reboot)s;'
                    'cd %(dir2)s; sh %(remove_route)s %(tunnel_route)s %(api_route)s;'
                    % {"dir":constant.AfterRebootConstant.REMOTE_ROUTE_SCRIPTS_DIR,
                       "script_after_reboot":"add_vpn_route_"+ self.cloud_params["azname"] +".sh",
                       "dir2":constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "remove_route": constant.RemoveConstant.REMOVE_ROUTE_SCRIPT,
                       "tunnel_route":
                           self.install_info["cascaded_subnets_info"]["tunnel_bearing"],
                       "api_route":
                           self.install_info["cascaded_subnets_info"]["external_api"]})
        except Exception as e:
            LOG.error("remove cascaded route error: %s", e.message)

    def remove_vpn_tunnel(self):
        vpn_conn_name = self.install_info["vpn_conn_name"]
        try:
            local_vpn = VPN(self.install_info["cascading_vpn_info"]["external_api_ip"],
                            constant.VpnConstant.VPN_ROOT,
                            constant.VpnConstant.VPN_ROOT_PWD)
            local_vpn.remove_tunnel(vpn_conn_name["api_conn_name"])
            local_vpn.remove_tunnel(vpn_conn_name["tunnel_conn_name"])
        except SSHCommandFailure:
            LOG.error("remove conn error.")
