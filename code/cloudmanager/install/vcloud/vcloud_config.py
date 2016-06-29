

import os
import pdb
from heat.openstack.common import log as logging
from heat.engine.resources.cloudmanager.vpn_configer import VpnConfiger
from heat.engine.resources.cloudmanager.vpn import VPN
import heat.engine.resources.cloudmanager.constant as constant
from vcloudcloudpersist import VcloudCloudDataHandler
import threading
import time
import heat.engine.resources.cloudmanager.proxy_manager
from heat.engine.resources.cloudmanager.cascading_configer import CascadingConfiger
from vcloud_cascaded_configer import CascadedConfiger

from heat.engine.resources.cloudmanager.commonutils import *
import heat.engine.resources.cloudmanager.exception as exception


LOG = logging.getLogger(__name__)

class VcloudCloudConfig:
    def __init__(self):
        self.local_vpn_thread = None
        self.cloud_vpn_thread = None
        self.cascading_thread = None
        self.cascaded_thread = None

        self.instal_info = None
        self.proxy_info = None
        self.installer = None
        self.cloudinfo = None
        self.vpn_conn_name =None
        self.cloud_params = None

    def initialize(self, cloud_params, instal_info, proxy_info, cloudinfo, installer):
        self.cloud_params = cloud_params
        self.instal_info = instal_info
        self.proxy_info = proxy_info
        self.installer = installer
        self.cloudinfo = cloudinfo
        self.vpn_conn_name = cloudinfo.get_vpn_conn_name()

    def config_vpn_only(self):
        LOG.info("config cloud vpn only")
        cloud_vpn_cf = VpnConfiger(
                    host_ip=self.instal_info["vpn"]["public_ip_vpn"],
                    user=constant.VpnConstant.VCLOUD_VPN_ROOT,
                    password=constant.VpnConstant.VCLOUD_VPN_ROOT_PWD)

        cloud_vpn_cf.register_add_conns(
                    tunnel_name=self.vpn_conn_name["api_conn_name"],
                    left_public_ip=self.instal_info["vpn"]["ext_net_publicip"],
                    left_subnet=self.instal_info["vdc_network"]["api_subnet_cidr"],
                    right_public_ip=self.installer.local_vpn_public_gw,
                    right_subnet=self.installer.local_api_subnet)

        cloud_vpn_cf.register_add_conns(
                    tunnel_name=self.vpn_conn_name["tunnel_conn_name"],
                    left_public_ip=self.instal_info["vpn"]["ext_net_publicip"],
                    left_subnet=self.instal_info["vdc_network"]["tunnel_subnet_cidr"],
                    right_public_ip=self.installer.local_vpn_public_gw,
                    right_subnet=self.installer.local_tunnel_subnet)
        cloud_vpn_cf.do_config()

    def config_vpn(self):
        if self.cloud_params['localmode'] == True :
            LOG.info("config local vpn")
            local_vpn_cf = VpnConfiger(
                    host_ip=self.installer.local_vpn_ip,
                    user=constant.VpnConstant.VPN_ROOT,
                    password=constant.VpnConstant.VPN_ROOT_PWD)

            local_vpn_cf.register_add_conns(
                    tunnel_name=self.vpn_conn_name["tunnel_conn_name"],
                    left_public_ip=self.installer.local_vpn_public_gw,
                    left_subnet=self.installer.local_tunnel_subnet,
                    right_public_ip=self.instal_info["vpn"]["public_ip_vpn"],
                    right_subnet=self.instal_info["vdc_network"]["tunnel_subnet_cidr"])
            local_vpn_cf.do_config()

            LOG.info("config vcloud vpn thread")
            cloud_vpn_cf = VpnConfiger(
                    host_ip=self.instal_info["vpn"]["public_ip_vpn"],
                    user=constant.VpnConstant.VCLOUD_VPN_ROOT,
                    password=constant.VpnConstant.VCLOUD_VPN_ROOT_PWD)

            cloud_vpn_cf.register_add_conns(
                    tunnel_name=self.vpn_conn_name["tunnel_conn_name"],
                    left_public_ip=self.instal_info["vpn"]["public_ip_vpn"],
                    left_subnet=self.instal_info["vdc_network"]["tunnel_subnet_cidr"],
                   right_public_ip=self.installer.local_vpn_public_gw,
                   right_subnet=self.installer.local_tunnel_subnet)
            cloud_vpn_cf.do_config()
        else :
            LOG.info("config local vpn")
            local_vpn_cf = VpnConfiger(
                    host_ip=self.installer.local_vpn_ip,
                    user=constant.VpnConstant.VPN_ROOT,
                    password=constant.VpnConstant.VPN_ROOT_PWD)

            local_vpn_cf.register_add_conns(
                    tunnel_name=self.vpn_conn_name["api_conn_name"],
                    left_public_ip=self.installer.local_vpn_public_gw,
                    left_subnet=self.installer.local_api_subnet,
                    right_public_ip=self.instal_info["vpn"]["ext_net_publicip"],
                    right_subnet=self.instal_info["vdc_network"]["api_subnet_cidr"])

            local_vpn_cf.register_add_conns(
                    tunnel_name=self.vpn_conn_name["tunnel_conn_name"],
                    left_public_ip=self.installer.local_vpn_public_gw,
                    left_subnet=self.installer.local_tunnel_subnet,
                    right_public_ip=self.instal_info["vpn"]["ext_net_publicip"],
                    right_subnet=self.instal_info["vdc_network"]["tunnel_subnet_cidr"])
            local_vpn_cf.do_config()

    def config_route(self):
        if self.cloud_params['localmode'] == True :
            LOG.info("add route to cascading ...")
            self._add_vpn_route(
                    host_ip=self.installer.cascading_api_ip,
                    user=constant.Cascading.ROOT,
                    passwd=constant.Cascading.ROOT_PWD,
                    access_cloud_tunnel_subnet=self.instal_info["vdc_network"]["tunnel_subnet_cidr"],
                    tunnel_gw=self.installer.local_vpn_tunnel_ip)

            check_host_status(
                        host=self.instal_info["cascaded"]["public_ip_api_reverse"],
                        user=constant.VcloudConstant.ROOT,
                        password=constant.VcloudConstant.ROOT_PWD,
                        retry_time=100, interval=3)    #waite cascaded vm started

            LOG.info("add route to vcloud on cascaded ...")
            self._add_vpn_route(
                    host_ip=self.instal_info["cascaded"]["public_ip_api_reverse"],
                    user=constant.VcloudConstant.ROOT,
                    passwd=constant.VcloudConstant.ROOT_PWD,
                    access_cloud_tunnel_subnet=self.installer.local_tunnel_subnet,
                    tunnel_gw=self.instal_info["vpn"]["vpn_tunnel_ip"])

        else :
             LOG.info("add route to cascading ...")
             self._add_vpn_route_with_api(
                    host_ip=self.installer.cascading_api_ip,
                    user=constant.Cascading.ROOT,
                    passwd=constant.Cascading.ROOT_PWD,
                    access_cloud_api_subnet=self.instal_info["vdc_network"]["api_subnet_cidr"],
                    api_gw=self.installer.local_vpn_api_ip,
                    access_cloud_tunnel_subnet=self.instal_info["vdc_network"]["tunnel_subnet_cidr"],
                    tunnel_gw=self.installer.local_vpn_tunnel_ip)

             LOG.info("add route to vcloud on cascaded ...")
             while True:
                 check_host_status(
                        host=self.instal_info["cascaded"]["tunnel_ip"],
                        user=constant.VcloudConstant.ROOT,
                        password=constant.VcloudConstant.ROOT_PWD,
                        retry_time=100, interval=3)    #waite cascaded vm started

                 self._add_vpn_route_with_api(
                        host_ip=self.instal_info["cascaded"]["tunnel_ip"],
                        user=constant.VcloudConstant.ROOT,
                        passwd=constant.VcloudConstant.ROOT_PWD,
                        access_cloud_api_subnet=self.installer.local_api_subnet,
                        api_gw=self.instal_info["vpn"]["vpn_api_ip"],
                        access_cloud_tunnel_subnet=self.installer.local_tunnel_subnet,
                        tunnel_gw=self.instal_info["vpn"]["vpn_tunnel_ip"])
                 try :
                     flag = check_host_status(
                            host=self.instal_info["cascaded"]["api_ip"],
                            user=constant.VcloudConstant.ROOT,
                            password=constant.VcloudConstant.ROOT_PWD,
                            retry_time=1, interval=1)    #test api net
                 except Exception:
                     continue    #add vpn route again

                 if flag :
                     break

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
        if self.cloud_params['localmode'] == True :
            cascaded_api_ip = self.instal_info["cascaded"]["public_ip_api_reverse"]
        else :
            cascaded_api_ip = self.instal_info["cascaded"]['api_ip']

        cascading_cf = CascadingConfiger(
                cascading_ip=self.installer.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cascaded_domain=self.cloudinfo.cascaded_domain,
                cascaded_api_ip=cascaded_api_ip,
                v2v_gw='1.1.1.1')
        cascading_cf.do_config()

    def config_cascaded(self):
        LOG.info("config cascaded")
        if self.cloud_params['localmode'] == True :
            cascaded_public_ip = self.instal_info["cascaded"]["public_ip_api_reverse"]
        else :
            cascaded_public_ip = self.instal_info["cascaded"]['tunnel_ip']

        cascaded_cf = CascadedConfiger(
                public_ip_api=cascaded_public_ip,
                api_ip=self.instal_info["cascaded"]["api_ip"],
                domain=self.cloudinfo.cascaded_domain,
                user=constant.VcloudConstant.ROOT,
                password=constant.VcloudConstant.ROOT_PWD,
                cascading_domain=self.installer.cascading_domain,
                cascading_api_ip=self.installer.cascading_api_ip)

        cascaded_cf.do_config()

    def config_proxy(self):
        # config proxy on cascading host
        #pdb.set_trace()
        LOG.info("config proxy ...")
        if self.proxy_info is None:
            LOG.info("wait proxy ...")
            self.proxy_info = self._get_proxy_retry()

        LOG.info("add dhcp to proxy ...")

        proxy_id = self.proxy_info["id"]
        proxy_num = self.proxy_info["proxy_num"]
        LOG.debug("proxy_id = %s, proxy_num = %s"
                     % (proxy_id, proxy_num))

        self._config_proxy(self.installer.cascading_api_ip, self.proxy_info)

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
        #TODO(lrx):modify to vcloud patch
        LOG.info("config patches config ...")
        #pdb.set_trace()
        if self.cloud_params['localmode'] == True :
            cascaded_public_ip = self.instal_info["cascaded"]["public_ip_api_reverse"]
        else :
            cascaded_public_ip = self.instal_info["cascaded"]['tunnel_ip']
        self._config_patch_tools(
                host_ip=self.installer.cascading_api_ip,
                user=constant.Cascading.ROOT,
                passwd=constant.Cascading.ROOT_PWD,
                cascaded_domain=self.cloudinfo.cascaded_domain,
                proxy_info=self.proxy_info,
                install_info=self.instal_info)

        self._config_vcloud(
                host_ip=cascaded_public_ip,
                user=constant.VcloudConstant.ROOT,
                passwd=constant.VcloudConstant.ROOT_PWD)


        self._deploy_patches(host_ip=self.installer.cascading_api_ip,
                             user=constant.Cascading.ROOT,
                             passwd=constant.Cascading.ROOT_PWD)

    def _config_patch_tools(self, host_ip, user, passwd,
                            cascaded_domain, proxy_info, install_info):
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
                           "cascading_domain": self.installer.cascading_domain})
                return True
            except Exception as e:
                LOG.error("config patch tool error, error: %s"
                             % e.message)
                continue
        return True

    def _config_vcloud(self,host_ip, user, passwd):
        for i in range(5):
            try:
                execute_cmd_without_stdout(
                    host=host_ip, user=user, password=passwd,
                    cmd='cd %(dis)s; sh %(script)s '
                        '%(vcloud_host_ip)s %(vcloud_org)s %(vcloud_vdc)s '
                        '%(vcloud_user)s %(vcloud_password)s '
                        % {"dis": constant.Cascaded.REMOTE_VCLOUD_SCRIPTS_DIR,
                           "script":
                               constant.Cascaded.CONFIG_VCLOUD_SCRIPT,
                           "vcloud_host_ip": self.installer.vcloud_url,
                           "vcloud_org": self.installer.vcloud_org,
                           "vcloud_vdc": self.installer.vcloud_vdc,
                           "vcloud_user": self.installer.username,
                           "vcloud_password": self.installer.passwd})

                return True
            except Exception as e:
                LOG.error("config vcloud error, error: %s"
                             % e.message)
                continue
        return True


    @staticmethod
    def _deploy_patches(host_ip, user, passwd):
        execute_cmd_without_stdout(
            host=host_ip, user=user, password=passwd,
            cmd='cd %s; python config.py cascading'
                % constant.PatchesConstant.PATCH_LUNCH_DIR)


        return True


    def config_storge(self):
        LOG.info("config storage...")
        #pdb.set_trace()
        if self.cloud_params['localmode'] == True :
            cascaded_api_ip = self.instal_info["cascaded"]["public_ip_api_reverse"]
        else :
            cascaded_api_ip = self.instal_info["cascaded"]['api_ip']
        self._config_storage(
                host=cascaded_api_ip,
                user=constant.VcloudConstant.ROOT,
                password=constant.VcloudConstant.ROOT_PWD,
                cascading_domain=self.installer.cascading_domain,
                cascaded_domain=self.cloudinfo.cascaded_domain,
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
                        % {"dir": constant.Cascaded.REMOTE_VCLOUD_SCRIPTS_DIR,
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


    #TODO(lrx):config the network between cloud and cloud
    def config_extnet(self):
        LOG.info("config ext net...")
        self._config_ext_network(cloud=self.cloudinfo, install_info=self.instal_info)

        if self.cloud_params['access']:
            try:
                self._enable_network_cross(
                        cloud=self.cloudinfo, cloud_install_info=self.instal_info)
            except Exception as e:
                    LOG.error("enable network cross error: %s"
                                 % e.message)

    def _config_ext_network(self, cloud, install_info):
        cascaded_tunnel_ip = install_info["cascaded"]["tunnel_ip"]
        eips = install_info["ext_net_eips"]
        vlan = vlan_manager.allocate_vlan()
        used_ip = [install_info["cascaded"]["api_ip"],
                   install_info["vpn"]["api_ip"],
                   install_info["v2v_gateway"]["ip"],
                   install_info["ceph_cluster"]["deploy_ip"],
                   install_info["ceph_cluster"]["node1_ip"],
                   install_info["ceph_cluster"]["node2_ip"],
                   install_info["ceph_cluster"]["node3_ip"]]

        self._update_l3_agent_conf(host_ip=cascaded_tunnel_ip,
                                   user=constant.Cascaded.ROOT,
                                   passwd=constant.Cascaded.ROOT_PWD,
                                   vcloud_region=cloud.get_region_id(),
                                   access_key=cloud.access_key,
                                   secret_key=cloud.secret_key,
                                   subnet_cidr=install_info["vpc"]["api_subnet_cidr"],
                                   interface_ip=install_info["cascaded"]["api_ip"],
                                   interface_id=install_info["cascaded"]["api_interface_id"],
                                   used_ips=used_ip)

        self._update_l3_proxy_code(proxy_ip=cloud.cloud_proxy["manageip"],
                                   user=constant.Proxy.USER,
                                   passwd=constant.Proxy.PWD,
                                   proxy_num=cloud.cloud_proxy["proxy_num"])

        self._update_external_api_vlan(
                host_ip=cascaded_tunnel_ip, user=constant.Cascaded.ROOT,
                passwd=constant.Cascaded.ROOT_PWD, vlan=vlan)

        self._create_ext_net(host_ip=self.installer.cascading_api_ip,
                             user=constant.Cascading.ROOT,
                             passwd=constant.Cascading.ROOT_PWD,
                             alias=cloud.az_alias, vlan=vlan)

        self._create_ext_subnet(host_ip=self.installer.cascading_api_ip,
                                user=constant.Cascading.ROOT,
                                passwd=constant.Cascading.ROOT_PWD,
                                alias=cloud.az_alias, eips=eips)

        proxy_num = cloud.cloud_proxy["proxy_num"]
        ext_net_name = "ext-%s-net" % cloud.az_alias
        self._update_proxy_params(host_ip=self.installer.cascading_api_ip,
                                  user=constant.Cascading.ROOT,
                                  passwd=constant.Cascading.ROOT_PWD,
                                  proxy_num=proxy_num,
                                  ext_net_name=ext_net_name)

    @staticmethod
    def _update_l3_agent_conf(host_ip, user, passwd,
                              vcloud_region, access_key, secret_key,
                              subnet_cidr, interface_ip, interface_id,
                              used_ips):
        for i in range(3):
            try:
                execute_cmd_without_stdout(
                        host=host_ip, user=user, password=passwd,
                        cmd="cd %(dir)s; "
                            "sh %(script)s "
                            "%(vcloud_region)s %(access_key)s %(secret_key)s "
                            "%(subnet_cidr)s %(interface_ip)s "
                            "%(interface_id)s %(used_ips)s"
                            % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                               "script": constant.Cascaded.UPDATE_L3_AGENT_SCRIPT,
                               "vcloud_region": vcloud_region,
                               "access_key": access_key,
                               "secret_key": secret_key,
                               "subnet_cidr": subnet_cidr,
                               "interface_ip": interface_ip,
                               "interface_id": interface_id,
                               "used_ips": ",".join(used_ips)})
                break
            except Exception as e:
                LOG.error("update l3 agent error, error: %s" % e.message)
                time.sleep(1)
                continue

    @staticmethod
    def _update_l3_proxy_code(proxy_ip, user, passwd, proxy_num):
        restart_proxy_cmd = "cps host-template-instance-operate " \
                            "--action stop " \
                            "--service neutron neutron-l3-%s; " \
                            "sleep 2s; " \
                            "cps host-template-instance-operate " \
                            "--action start " \
                            "--service neutron neutron-l3-%s" \
                            % (proxy_num, proxy_num)
        for i in range(3):
            try:
                scp_file_to_host(host=proxy_ip, user=user, password=passwd,
                                 file_name=constant.Proxy.L3_PROXY_CODE,
                                 local_dir=constant.Proxy.LOCAL_NEUTRON_PROXY_DIR,
                                 remote_dir=constant.Proxy.REMOTE_NEUTRON_PROXY_DIR)

                execute_cmd_without_stdout(
                        host=proxy_ip, user=user, password=passwd,
                        cmd=restart_proxy_cmd)
                LOG.info("update l3 proxy code success.")
                return True
            except Exception as e:
                LOG.error("update l3 proxy code error, "
                             "proxy_ip: %s, proxy_num: %s. error: %s"
                             % (proxy_ip, proxy_num, e.message))
        LOG.error("update l3 proxy code failed, please check it."
                     "proxy_ip: %s, proxy_num: %s." % (proxy_ip, proxy_num))
        return False

    @staticmethod
    def _update_external_api_vlan(host_ip, user, passwd, vlan):
        for i in range(3):
            try:
                execute_cmd_without_stdout(
                        host=host_ip, user=user, password=passwd,
                        cmd='cd %(dir)s;'
                            'sh %(update_network_vlan_script)s '
                            '%(network_name)s %(vlan)s'
                            % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                               "update_network_vlan_script":
                                   constant.Cascaded.UPDATE_NETWORK_VLAN_SCRIPT,
                               "network_name": "external_api",
                               "vlan": vlan})
                break
            except Exception as e:
                LOG.error("update network vlan error, vlan: %s, error: %s "
                             % (vlan, e.message))
                time.sleep(1)
                continue

    def _create_ext_net(host_ip, user, passwd, alias, vlan):
        ext_net_name = "ext-%s-net" % alias
        create_net_cmd = ". /root/adminrc;" \
                         "neutron net-delete %(ext_net_name)s; " \
                         "neutron net-create %(ext_net_name)s " \
                         "--router:external " \
                         "--provider:physical_network physnet2 " \
                         "--provider:network_type vlan " \
                         "--provider:segmentation_id %(vlan)s" \
                         % {"ext_net_name": ext_net_name,
                            "vlan": vlan}
        for i in range(3):
            try:
                execute_cmd_without_stdout(host=host_ip, user=user,
                                           password=passwd, cmd=create_net_cmd)
                break
            except Exception as e:
                LOG.error("create ext network error, vlan: %s, error: %s "
                             % (vlan, e.message))
                time.sleep(1)
                continue

    @staticmethod
    def _create_ext_subnet(host_ip, user, passwd, alias, eips):
        if not eips:
            return False

        ext_cidr = "%s.0.0.0/8" % eips[0].split(".")[0]
        ext_net_name = "ext-%s-net" % alias
        ext_subnet_name = "ext-%s-subnet" % alias

        create_subnet_cmd = ". /root/adminrc; " \
                            "neutron subnet-create %(ext_net_name)s " \
                            "%(net_cidr)s --name %(ext_subnet_name)s" \
                            % {"ext_net_name": ext_net_name,
                               "net_cidr": ext_cidr,
                               "ext_subnet_name": ext_subnet_name}

        for eip in eips:
            create_subnet_cmd += ' --allocation-pool start=%s,end=%s' \
                                 % (eip, eip)

        create_subnet_cmd += ' --disable-dhcp --no-gateway'

        for i in range(3):
            try:
                execute_cmd_without_stdout(host=host_ip, user=user,
                                           password=passwd,
                                           cmd=create_subnet_cmd)
                break
            except Exception as e:
                LOG.error("create ext subnet error, alias: %s, "
                             "ext_cidr: %s, used_ips: %s. error: %s"
                             % (alias, ext_cidr, eips, e.message))
                time.sleep(1)
                continue

    @staticmethod
    def _update_proxy_params(host_ip, user, passwd, proxy_num, ext_net_name):
        for i in range(3):
            try:
                execute_cmd_without_stdout(
                        host=host_ip, user=user, password=passwd,
                        cmd="cd %(dir)s; "
                            "sh %(script)s %(proxy_num)s %(ext_net_num)s"
                            % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                               "script": constant.Cascading.UPDATE_PROXY_PARAMS,
                               "proxy_num": proxy_num,
                               "ext_net_num": ext_net_name})
                break
            except Exception as e:
                LOG.error("update proxy params error, proxy_num: %s, "
                             "ext_net_name: %s"
                             % (proxy_num, ext_net_name))
                time.sleep(1)
                continue

    @staticmethod
    def _enable_network_cross(self, cloud, cloud_install_info):
        #TODO(lrx):add installer functions
        cloud_id = cloud.cloud_id
        vpc_info = cloud_install_info["vpc"]
        vpn_info = cloud_install_info["vpn"]
        cascaded_info = cloud_install_info["cascaded"]
        vpn = VPN(public_ip=vpn_info["eip_public_ip"],
                  user=VpnConstant.VCLOUD_VPN_ROOT,
                  pass_word=VpnConstant.VCLOUD_VPN_ROOT_PWD)

        for other_cloud_id in VcloudCloudDataHandler().list_vcloud_clouds():
            if other_cloud_id == cloud_id:
                continue

            other_cloud = VcloudCloudDataHandler().get_vcloud_cloud(other_cloud_id)
            other_cloud_install_info = \
                self.installer.get_vcloud_access_cloud_install_info(other_cloud_id)
            if not other_cloud.access:
                continue

            other_vpc_info = other_cloud_install_info["vpc"]
            other_vpn_info = other_cloud_install_info["vpn"]
            other_cascaded_info = other_cloud_install_info["cascaded"]
            other_vpn = VPN(public_ip=other_vpn_info["eip_public_ip"],
                            user=VpnConstant.VCLOUD_VPN_ROOT,
                            pass_word=VpnConstant.VCLOUD_VPN_ROOT_PWD)

            LOG.info("add conn on api vpns...")
            api_conn_name = "%s-api-%s" % (cloud_id, other_cloud_id)
            vpn.add_tunnel(tunnel_name=api_conn_name,
                           left=vpn_info["eip_public_ip"],
                           left_subnet=vpc_info["api_subnet_cidr"],
                           right=other_vpn_info["eip_public_ip"],
                           right_subnet=other_vpc_info["api_subnet_cidr"])

            other_vpn.add_tunnel(tunnel_name=api_conn_name,
                                 left=other_vpn_info["eip_public_ip"],
                                 left_subnet=other_vpc_info["api_subnet_cidr"],
                                 right=vpn_info["eip_public_ip"],
                                 right_subnet=vpc_info["api_subnet_cidr"])

            LOG.info("add conn on tunnel vpns...")
            tunnel_conn_name = "%s-tunnel-%s" % (cloud_id, other_cloud_id)
            vpn.add_tunnel(tunnel_name=tunnel_conn_name,
                           left=vpn_info["eip_public_ip"],
                           left_subnet=vpc_info["tunnel_subnet_cidr"],
                           right=other_vpn_info["eip_public_ip"],
                           right_subnet=other_vpc_info["tunnel_subnet_cidr"])

            other_vpn.add_tunnel(tunnel_name=tunnel_conn_name,
                                 left=other_vpn_info["eip_public_ip"],
                                 left_subnet=other_vpc_info["tunnel_subnet_cidr"],
                                 right=vpn_info["eip_public_ip"],
                                 right_subnet=vpc_info["tunnel_subnet_cidr"])

            vpn.restart_ipsec_service()
            other_vpn.restart_ipsec_service()

            LOG.info("add route on openstack cascadeds...")
            execute_cmd_without_stdout(
                host=cascaded_info["tunnel_ip"],
                user=constant.Cascaded.ROOT,
                password=constant.Cascaded.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
                    % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                       "script": constant.Cascaded.ADD_API_ROUTE_SCRIPT,
                       "subnet": other_vpc_info["api_subnet_cidr"],
                       "gw": vpn_info["api_ip"]})

            execute_cmd_without_stdout(
                host=other_cascaded_info["tunnel_ip"],
                user=constant.Cascaded.ROOT,
                password=constant.Cascaded.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
                    % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                       "script": constant.Cascaded.ADD_API_ROUTE_SCRIPT,
                       "subnet": vpc_info["api_subnet_cidr"],
                       "gw": other_vpn_info["api_ip"]})

            # add cloud-sg
            LOG.info("add vcloud sg...")
            self.installer.vcloud_access_cloud_add_security(
                region=cloud.get_region_id(),
                az=cloud.az,
                access_key=cloud.access_key,
                secret_key=cloud.secret_key,
                cidr="%s/32" % other_vpn_info["eip_public_ip"])

            self.installer.vcloud_access_cloud_add_security(
                region=other_cloud.get_region_id(),
                az=cloud.az,
                access_key=other_cloud.access_key,
                secret_key=other_cloud.secret_key,
                cidr="%s/32" % vpn_info["eip_public_ip"])

        return True

    def remove_existed_cloud(self):
        #config cascading unregister
        #TODO(lrx):modify remove aggregate
        # try:
        #     execute_cmd_without_stdout(
        #         host=self.installer.cascading_api_ip,
        #         user=constant.Cascading.ROOT,
        #         password=constant.Cascading.ROOT_PWD,
        #         cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
        #             % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
        #                "script":
        #                    constant.RemoveConstant.REMOVE_AGGREGATE_SCRIPT,
        #                "cascaded_domain": self.cloudinfo.cascaded_domain})
        # except Exception as e:
        #     LOG.error("remove aggregate error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(
                host=self.installer.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_CINDER_SERVICE_SCRIPT,
                       "cascaded_domain": self.cloudinfo.cascaded_domain})
        except Exception as e:
            LOG.error("remove cinder service error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(
                host=self.installer.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
                       "cascaded_domain": self.cloudinfo.cascaded_domain})

            execute_cmd_without_stdout(
                host=self.installer.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(proxy_host)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
                       "proxy_host": self.cloudinfo.cloud_proxy["id"]})

        except Exception as e:
            LOG.error("remove neutron agent error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(
                host=self.installer.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.RemoveConstant.REMOVE_KEYSTONE_SCRIPT,
                       "cascaded_domain": self.cloudinfo.cascaded_domain})
        except SSHCommandFailure:
            LOG.error("remove keystone endpoint error.")

        try:
            execute_cmd_without_stdout(
                host=self.installer.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; '
                    'sh %(script)s %(proxy_host_name)s %(proxy_num)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.RemoveConstant.REMOVE_PROXY_SCRIPT,
                       "proxy_host_name": self.cloudinfo.cloud_proxy["id"],
                       "proxy_num": self.cloudinfo.cloud_proxy["proxy_num"]})
        except SSHCommandFailure:
            LOG.error("remove proxy error.")

        if self.cloud_params['localmode'] == True :
            cascaded_api_ip = self.instal_info["cascaded"]["public_ip_api_reverse"]
        else :
            cascaded_api_ip = self.instal_info["cascaded"]['api_ip']

        address = "/%(cascaded_domain)s/%(cascaded_ip)s" \
                  % {"cascaded_domain": self.cloudinfo.cascaded_domain,
                     "cascaded_ip": cascaded_api_ip}

        try:
            execute_cmd_without_stdout(
                host=self.installer.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s remove %(address)s'
                    % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.PublicConstant.MODIFY_DNS_SERVER_ADDRESS,
                       "address": address})
        except SSHCommandFailure:
            LOG.error("remove dns address error.")

        # config local_vpn
        vpn_conn_name = self.cloudinfo.get_vpn_conn_name()
        try:
            local_vpn = VPN(self.installer.local_vpn_ip,
                            constant.VpnConstant.VPN_ROOT,
                            constant.VpnConstant.VPN_ROOT_PWD)

            local_vpn.remove_tunnel(vpn_conn_name["tunnel_conn_name"])
        except SSHCommandFailure:
            LOG.error("remove conn error.")

