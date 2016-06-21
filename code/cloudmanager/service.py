# -*- coding:utf-8 -*-

__author__ = 'q00222219@huawei'

import threading

import awscloud
import constant
import install.aws_access_cloud_installer as cascaded_installer

#import fs_gateway_register
from vpn import VPN
from commonutils import *
from environmentinfo import *
from awscloudpersist import AwsCloudDataHandler
import proxy_manager
from subnet_manager import SubnetManager
from region_mapping import *
from constant import *
from vpn_configer import VpnConfiger
from cascading_configer import CascadingConfiger
from cascaded_configer import CascadedConfiger
from hypernode_manager.hypernode_manager import HyperNodeManager
import vlan_manager

from heat.openstack.common import log as logging
LOG = logging.getLogger(__name__)

import os

class CloudManager:
    def __init__(self):
        self._read_env()
        self.cloud_cascaded = None
        self.cloud_vpn = None
        self.proxy_info = None
        self.local_vpn_thread = None
        self.cloud_vpn_thread = None
        self.cascading_thread = None
        self.cascaded_thread = None

    def _read_env(self):
        try:
            env_info = read_environment_info()
            self.env = env_info["env"]
            self.cascading_api_ip = env_info["cascading_api_ip"]
            self.cascading_domain = env_info["cascading_domain"]
            self.local_vpn_ip = env_info["local_vpn_ip"]
            self.local_vpn_public_gw = env_info["local_vpn_public_gw"]
            self.cascading_eip = env_info["cascading_eip"]
            self.local_api_subnet = env_info["local_api_subnet"]
            self.local_vpn_api_ip = env_info["local_vpn_api_ip"]
            self.local_tunnel_subnet = env_info["local_tunnel_subnet"]
            self.local_vpn_tunnel_ip = env_info["local_vpn_tunnel_ip"]
            self.existed_cascaded = env_info["existed_cascaded"]
        except ReadEnvironmentInfoFailure as e:
            LOG.error(
                "read environment info error. check the config file: %s"
                % e.message)
            raise ReadEnvironmentInfoFailure(error=e.message)

    def add_aws_access_cloud(self, region_name, az, az_alias,
                             access_key, secret_key, access=True,
                             driver_type="agent", with_ceph=True):
        start_time = time.time()

        cloud_id = "@".join([access_key, region_name, az])
        LOG.info("start add aws access cloud, "
                    "region_name=%s, az=%s, az_alias=%s, access_key=%s, "
                    "access=%s, driver_type=%s, with_ceph=%s"
                    % (region_name, az, az_alias, access_key,
                       access, driver_type, with_ceph))

        # distribute cloud_domain && proxy_name for this cloud
        proxy_info = proxy_manager.distribute_proxy()

        # distribute vpn_subnet && hn_subnet for this cloud
        cloud_subnet = self._distribute_cidr_for_cloud()

        # install base environment
        if self.local_vpn_public_gw == self.cascading_eip:
            green_ips = [self.local_vpn_public_gw]
        else:
            green_ips = [self.local_vpn_public_gw, self.cascading_eip]

        aws_install_info = cascaded_installer.aws_access_cloud_install(
                cloud_id=cloud_id,
                region=get_region_id(region_name),
                az=az,
                access_key=access_key,
                secret_key=secret_key,
                api_cidr=cloud_subnet["cloud_api"],
                tunnel_cidr=cloud_subnet["cloud_tunnel"],
                ceph_cidr=cloud_subnet["cloud_api"],
                green_ips=green_ips,
                local_api_cidr=self.local_api_subnet,
                local_tunnel_cidr=self.local_tunnel_subnet)

        if aws_install_info is None:
            LOG.error("install aws cascaded vm and vpn vm error.")
            raise InstallAWSAccessCloudFailure(error="aws cloud info is null.")
        else:
            LOG.info("install aws cascaded vm and vpn vm success.")

        # create a aws access cloud.
        cascaded_domain = self._distribute_cloud_domain(
                region_name=region_name, az_alias=az_alias, az_tag="--aws")
        cloud = awscloud.AwsCloud(
                cloud_id=cloud_id,
                access_key=access_key,
                secret_key=secret_key,
                region_name=region_name,
                az=az,
                az_alias=az_alias,
                cascaded_domain=cascaded_domain,
                cascaded_eip=aws_install_info["cascaded"]["eip_public_ip"],
                vpn_eip=aws_install_info["vpn"]["eip_public_ip"],
                cloud_proxy=proxy_info,
                driver_type=driver_type,
                access=access,
                with_ceph=with_ceph)

        vpn_conn_name = cloud.get_vpn_conn_name()
        # config local_vpn.
        LOG.info("config local vpn thread")
        local_vpn_cf = VpnConfiger(
                host_ip=self.local_vpn_ip,
                user=constant.VpnConstant.VPN_ROOT,
                password=constant.VpnConstant.VPN_ROOT_PWD)

        local_vpn_cf.register_add_conns(
                tunnel_name=vpn_conn_name["api_conn_name"],
                left_public_ip=self.local_vpn_public_gw,
                left_subnet=self.local_api_subnet,
                right_public_ip=aws_install_info["vpn"]["eip_public_ip"],
                right_subnet=aws_install_info["vpc"]["api_subnet_cidr"])

        local_vpn_cf.register_add_conns(
                tunnel_name=vpn_conn_name["tunnel_conn_name"],
                left_public_ip=self.local_vpn_public_gw,
                left_subnet=self.local_tunnel_subnet,
                right_public_ip=aws_install_info["vpn"]["eip_public_ip"],
                right_subnet=aws_install_info["vpc"]["tunnel_subnet_cidr"])

        self.local_vpn_thread = threading.Thread(
                target=local_vpn_cf.do_config)

        LOG.info("config cloud vpn thread")
        cloud_vpn_cf = VpnConfiger(
                host_ip=aws_install_info["vpn"]["eip_public_ip"],
                user=constant.VpnConstant.AWS_VPN_ROOT,
                password=constant.VpnConstant.AWS_VPN_ROOT_PWD)

        cloud_vpn_cf.register_add_conns(
                tunnel_name=vpn_conn_name["api_conn_name"],
                left_public_ip=aws_install_info["vpn"]["eip_public_ip"],
                left_subnet=aws_install_info["vpc"]["api_subnet_cidr"],
                right_public_ip=self.local_vpn_public_gw,
                right_subnet=self.local_api_subnet)

        cloud_vpn_cf.register_add_conns(
                tunnel_name=vpn_conn_name["tunnel_conn_name"],
                left_public_ip=aws_install_info["vpn"]["eip_public_ip"],
                left_subnet=aws_install_info["vpc"]["tunnel_subnet_cidr"],
                right_public_ip=self.local_vpn_public_gw,
                right_subnet=self.local_tunnel_subnet)

        self.cloud_vpn_thread = threading.Thread(
                target=cloud_vpn_cf.do_config)

        LOG.info("config cascading thread")
        cascading_cf = CascadingConfiger(
                cascading_ip=self.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cascaded_domain=cascaded_domain,
                cascaded_api_ip=aws_install_info["cascaded"]["api_ip"],
                v2v_gw=aws_install_info["v2v_gateway"]["ip"])

        self.cascading_thread = threading.Thread(
                target=cascading_cf.do_config)

        LOG.info("config cascaded thread")
        cascaded_cf = CascadedConfiger(
                api_ip=aws_install_info["cascaded"]["api_ip"],
                tunnel_ip=aws_install_info["cascaded"]["tunnel_ip"],
                domain=cascaded_domain,
                user=constant.Cascaded.ROOT,
                password=constant.Cascaded.ROOT_PWD,
                cascading_domain=self.cascading_domain,
                cascading_api_ip=self.cascading_api_ip)

        self.cascaded_thread = threading.Thread(
                target=cascaded_cf.do_config)

        cost_time = time.time() - start_time
        LOG.info("start all thread, cost time: %d" % cost_time)
        self._start_all_threads()

        LOG.info("add route to aws on cascading ...")
        self._add_vpn_route(
                host_ip=self.cascading_api_ip,
                user=constant.Cascading.ROOT,
                passwd=constant.Cascading.ROOT_PWD,
                access_cloud_api_subnet=aws_install_info["vpc"]["api_subnet_cidr"],
                api_gw=self.local_vpn_api_ip,
                access_cloud_tunnel_subnet=aws_install_info["vpc"]["tunnel_subnet_cidr"],
                tunnel_gw=self.local_vpn_tunnel_ip)

        LOG.info("add route to aws on existed cascaded ...")
        for host in self.existed_cascaded:
            self._add_vpn_route(
                    host_ip=host,
                    user=constant.Cascading.ROOT,
                    passwd=constant.Cascading.ROOT_PWD,
                    access_cloud_api_subnet=aws_install_info["vpc"]["api_subnet_cidr"],
                    api_gw=self.local_vpn_api_ip,
                    access_cloud_tunnel_subnet=aws_install_info["vpc"]["tunnel_subnet_cidr"],
                    tunnel_gw=self.local_vpn_tunnel_ip)

        # config proxy on cascading host
        if proxy_info is None:
            LOG.info("wait proxy ...")
            proxy_info = self._get_proxy_retry()

        LOG.info("add dhcp to proxy ...")
        cloud.cloud_proxy = proxy_info
        proxy_id = proxy_info["id"]
        proxy_num = proxy_info["proxy_num"]
        LOG.debug("proxy_id = %s, proxy_num = %s"
                     % (proxy_id, proxy_num))

        self._config_proxy(self.cascading_api_ip, proxy_info)

        AwsCloudDataHandler().add_aws_cloud(cloud)

        LOG.info("config patches config ...")
        self._config_patch_tools(
                host_ip=self.cascading_api_ip,
                user=constant.Cascading.ROOT,
                passwd=constant.Cascading.ROOT_PWD,
                cascaded_domain=cascaded_domain,
                proxy_info=proxy_info,
                install_info=aws_install_info)

        self._config_aws_patches(
                host_ip=self.cascading_api_ip, user=constant.Cascading.ROOT,
                passwd=constant.Cascading.ROOT_PWD,
                region=cloud.get_region_id(), az=az,
                access_key=access_key, secret_key=secret_key,
                install_info=aws_install_info, driver_type=driver_type)

        cost_time = time.time() - start_time
        LOG.info("wait all thread success, cost time: %d" % cost_time)
        self._join_all_threads()

        cost_time = time.time() - start_time
        LOG.info("config success, cost time: %d" % cost_time)
        self._deploy_patches(host_ip=self.cascading_api_ip,
                             user=constant.Cascading.ROOT,
                             passwd=constant.Cascading.ROOT_PWD)

        LOG.info("config storage...")
        self._config_storage(
                host_ip=aws_install_info["cascaded"]["api_ip"],
                user=constant.Cascaded.ROOT,
                password=constant.Cascaded.ROOT_PWD,
                cascading_domain=self.cascading_domain,
                cascaded_domain=cascaded_domain,
                install_info=aws_install_info)

        LOG.info("config ext net...")
        self._config_ext_network(cloud=cloud, install_info=aws_install_info)

        if access:
            try:
                self._enable_network_cross(
                        cloud=cloud, cloud_install_info=aws_install_info)
            except Exception as e:
                    LOG.error("enable network cross error: %s"
                                 % e.message)

        cost_time = time.time() - start_time
        LOG.info("success, cost time: %d" % cost_time)

        return True

    
    @staticmethod
    def _update_cascaded_code(cascaded_ip, cascaded_user_name, cascaded_user_passwd):  
        restart_glance_cmd = "cps host-template-instance-operate --action stop --service glance glance; " \
                              "sleep 4s; " \
                              "cps host-template-instance-operate --action start --service glance glance;"
                              
        restart_cinder_api_cmd = "cps host-template-instance-operate --action stop --service cinder cinder-api; " \
                              "sleep 4s; " \
                              "cps host-template-instance-operate --action start --service cinder cinder-api;"
                              
        for i in range(5):                          
            try:
                scp_file_to_host(host=cascaded_ip, user=cascaded_user_name, password=cascaded_user_passwd,
                                 file_name=constant.FsCascaded.GLANCE_CODE,
                                 local_dir=constant.FsCascaded.LOCAL_GLANCE_DIR,
                                 remote_dir=constant.FsCascaded.REMOTE_GLANCE_DIR)
    
                execute_cmd_without_stdout(
                        host=cascaded_ip, user=cascaded_user_name, password=cascaded_user_passwd,
                        cmd=restart_glance_cmd)
                LOG.info("update glance code success.")
                
                scp_file_to_host(host=cascaded_ip, user=cascaded_user_name, password=cascaded_user_passwd,
                                 file_name=constant.FsCascaded.CINDER_VOLUME_API_CODE,
                                 local_dir=constant.FsCascaded.LOCAL_CINDER_DIR,
                                 remote_dir=constant.FsCascaded.REMOTE_CINDER_DIR)
    
                execute_cmd_without_stdout(
                        host=cascaded_ip, user=cascaded_user_name, password=cascaded_user_passwd,
                        cmd=restart_cinder_api_cmd)
                LOG.info("update cinder api  code success.")
                
                return True
                
            except Exception as e:
                LOG.error("update cascaded code error, "
                             "cascaded_ip: %s, error: %s"
                             % (cascaded_ip,  e.message))
        LOG.error("update cascaded code failed, please check it."
                     "cascaded_ip: %s" % (cascaded_ip))
        return False
    
    @staticmethod
    def _copy_add_route_sh_to_fscascaded(cascaded_ip, cascaded_user_name, cascaded_user_passwd):   
        for i in range(5):                          
            try:
                mkdir_cmd = "mkdir -p " + constant.FsCascaded.REMOTE_SCRIPTS_DIR
                execute_cmd_without_stdout(
                        host=cascaded_ip, user=cascaded_user_name, password=cascaded_user_passwd,
                        cmd=mkdir_cmd)
                
                scp_file_to_host(host=cascaded_ip, user=cascaded_user_name, password=cascaded_user_passwd,
                                 file_name=constant.Cascading.ADD_VPN_ROUTE_SCRIPT,
                                 local_dir=constant.Cascading.REMOTE_SCRIPTS_DIR,
                                 remote_dir=constant.FsCascaded.REMOTE_SCRIPTS_DIR)
                return True
                
            except Exception as e:
                LOG.error("copy add_vpn_route.sh code to cascaded error, "
                             "cascaded_ip: %s, error: %s"
                             % (cascaded_ip,  e.message))
        LOG.error("copy add_vpn_route.sh code to cascaded failed, please check it."
                     "cascaded_ip: %s" % (cascaded_ip))
        return False
    
    
    @staticmethod
    def _update_cinder_proxy_code(proxy_ip, user, passwd, proxy_num):
        restart_proxy_cmd = "cps host-template-instance-operate " \
                            "--action stop " \
                            "--service cinder cinder-%s; " \
                            "sleep 2s; " \
                            "cps host-template-instance-operate " \
                            "--action start " \
                            "--service cinder cinder-%s" \
                            % (proxy_num, proxy_num)
        for i in range(3):
            try:
                scp_file_to_host(host=proxy_ip, user=user, password=passwd,
                                 file_name=constant.Proxy.CINDER_PROXY_CODE,
                                 local_dir=constant.Proxy.LOCAL_CINDER_PROXY_DIR,
                                 remote_dir=constant.Proxy.REMOTE_CINDER_PROXY_DIR)

                execute_cmd_without_stdout(
                        host=proxy_ip, user=user, password=passwd,
                        cmd=restart_proxy_cmd)
                LOG.info("update cinder proxy code success.")
                return True
            except Exception as e:
                LOG.error("update cinder proxy code error, "
                             "proxy_ip: %s, proxy_num: %s. error: %s"
                             % (proxy_ip, proxy_num, e.message))
        LOG.error("update cinder proxy code failed, please check it."
                     "proxy_ip: %s, proxy_num: %s." % (proxy_ip, proxy_num))
        return False
        

    def _start_all_threads(self):
        self.local_vpn_thread.start()
        self.cloud_vpn_thread.start()
        self.cascading_thread.start()
        self.cascaded_thread.start()

    def _join_all_threads(self):
        self.local_vpn_thread.join()
        self.cloud_vpn_thread.join()
        self.cascading_thread.join()
        self.cascaded_thread.join()

    def _distribute_cloud_domain(self, region_name, az_alias, az_tag):
        """distribute cloud domain
        :return:
        """
        domain_list = self.cascading_domain.split(".")
        domainpostfix = ".".join([domain_list[2], domain_list[3]])
        l_region_name = region_name.lower()
        cloud_cascaded_domain = ".".join(
                [az_alias, l_region_name + az_tag, domainpostfix])
        return cloud_cascaded_domain

    @staticmethod
    def _distribute_cidr_for_cloud():
        cloud_subnet = SubnetManager().distribute_subnet_pair()
        cloud_subnet["hynode_control"] = "172.29.251.0/24"
        cloud_subnet["hynode_data"] = "172.29.252.0/24"
        return cloud_subnet

    @staticmethod
    def _add_vpn_route(host_ip, user, passwd,
                       access_cloud_api_subnet, api_gw,
                       access_cloud_tunnel_subnet, tunnel_gw):
        try:
            execute_cmd_without_stdout(
                host=host_ip,
                user=user,
                password=passwd,
                cmd='cd %(dir)s; sh %(script)s '
                    '%(access_cloud_api_subnet)s %(api_gw)s '
                    '%(access_cloud_tunnel_subnet)s %(tunnel_gw)s'
                    % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                       "script": constant.Cascading.ADD_VPN_ROUTE_SCRIPT,
                       "access_cloud_api_subnet": access_cloud_api_subnet,
                       "api_gw": api_gw,
                       "access_cloud_tunnel_subnet": access_cloud_tunnel_subnet,
                       "tunnel_gw": tunnel_gw})
        except SSHCommandFailure:
            LOG.error("add vpn route error, host: %s" % host_ip)
            return False
        return True
    
    @staticmethod
    def _add_vpn_tunnel_route(host_ip, user, passwd,access_cloud_tunnel_subnet, tunnel_gw):
        try:
            execute_cmd_without_stdout(
                host=host_ip,
                user=user,
                password=passwd,
                cmd='cd %(dir)s; sh %(script)s '
                    '%(access_cloud_tunnel_subnet)s %(tunnel_gw)s'
                    % {"dir": constant.Cascading.REMOTE_SCRIPTS_DIR,
                       "script": constant.Cascading.ADD_VPN_ROUTE_TUNNEL_SCRIPT,
                       "access_cloud_tunnel_subnet": access_cloud_tunnel_subnet,
                       "tunnel_gw": tunnel_gw})
        except SSHCommandFailure:
            LOG.error("add vpn tunnel route error, host: %s" % host_ip)
            return False
        return True
    
    @staticmethod
    def _update_fsgateway_config(host_ip, user, passwd,
                       action, region,keystone_url=None):
        try:
            execute_cmd_without_stdout(
                host=host_ip,
                user=user,
                password=passwd,
                cmd='cd %(dir)s; sh %(script)s %(action)s %(region)s %(keystone_url)s'
                    % {"dir":constant.Cascading.REMOTE_SCRIPTS_DIR,
                       "script":'fs_gateway_conf_update.sh',
                       "action": action,
                       "region": region,
                       "keystone_url": keystone_url})
        except SSHCommandFailure:
            LOG.error("_update_fsgateway_config action %s, region %s url %s,  host: %s" % (action, region, keystone_url, host_ip))
            return False
        return True

    @staticmethod
    def _get_proxy_retry():
        LOG.info("get proxy retry ...")
        proxy_info = proxy_manager.distribute_proxy()
        for i in range(10):
            if proxy_info is None:
                time.sleep(240)
                proxy_info = proxy_manager.distribute_proxy()
            else:
                return proxy_info
        raise ConfigProxyFailure(error="check proxy config result failed")

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
            except SSHCommandFailure:
                LOG.error("config proxy error, try again...")
        return True

    def _config_patch_tools(self, host_ip, user, passwd,
                            cascaded_domain, proxy_info, install_info):
        for i in range(10):
            try:
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
                           "local_api_subnet": self.local_api_subnet,
                           "cloud_vpn_api_ip": install_info["vpn"]["api_ip"],
                           "local_tunnel_subnet": self.local_tunnel_subnet,
                           "cloud_vpn_tunnel_ip": install_info["vpn"]["tunnel_ip"],
                           "cascading_domain": self.cascading_domain})
                return True
            except Exception as e:
                LOG.error("config patch tool error, error: %s"
                             % e.message)
                continue
        return True

    def _config_aws_patches(self, host_ip, user, passwd,
                            region, az, access_key, secret_key,
                            install_info, driver_type,
                            hynode_control_cidr="172.29.251.0/24",
                            hynode_data_cidr="172.29.252.0/24"):
        local_api_subnet = self.local_api_subnet
        cloud_vpn_api_ip = install_info["vpn"]["api_ip"]
        local_tunnel_subnet = self.local_tunnel_subnet
        cloud_vpn_tunnel_ip = install_info["vpn"]["tunnel_ip"]
        cascaded_ip = install_info["cascaded"]["api_ip"]
        cloud_api_subnet_id = install_info["vpc"]["api_subnet_id"]
        cloud_tunnel_subnet_id = install_info["vpc"]["tunnel_subnet_id"]

        hynode_ami_id = "hynode_ami_id"
        if "hynode" in install_info.keys():
            hynode_ami_id = install_info["hynode"]["ami_id"]

        vpc_id = install_info["vpc"]["vpc_id"]

        cgw_id = install_info["v2v_gateway"]["vm_id"]
        cgw_ip = install_info["v2v_gateway"]["ip"]
        internal_base_subnet_id = install_info["vpc"]["base_subnet_id"]
        internal_base_ip = install_info["cascaded"]["base_ip"]
        cascading_domain = self.cascading_domain

        for i in range(10):
            try:
                execute_cmd_without_stdout(
                    host=host_ip, user=user, password=passwd,
                    cmd='cd %s; '
                        'sh config_aws.sh %s %s %s %s %s %s %s %s %s '
                        '%s %s %s %s %s %s %s %s %s %s %s %s'
                        % (constant.PatchesConstant.REMOTE_SCRIPTS_DIR,
                           access_key, secret_key, region, az,
                           cloud_api_subnet_id, cloud_tunnel_subnet_id,
                           cgw_id, cgw_ip,
                           cascaded_ip,
                           local_api_subnet, cloud_vpn_api_ip,
                           local_tunnel_subnet, cloud_vpn_tunnel_ip,
                           hynode_control_cidr, hynode_data_cidr,
                           internal_base_subnet_id,
                           hynode_ami_id, vpc_id,
                           internal_base_ip,
                           cascading_domain,
                           driver_type))
                break
            except Exception as e:
                LOG.error("conf aws file error, error: %s" % e.message)
                continue

        for i in range(10):
            try:
                execute_cmd_without_stdout(
                    host=host_ip, user=user,password=passwd,
                    cmd='cd %s;sh config_add_route.sh '
                        '%s %s %s %s'
                        % (constant.PatchesConstant.REMOTE_SCRIPTS_DIR,
                           local_api_subnet, cloud_vpn_api_ip,
                           local_tunnel_subnet, cloud_vpn_tunnel_ip))
                break
            except Exception as e:
                LOG.error("conf route error, error: %s"
                             % e.message)
                continue
        return True

    @staticmethod
    def _deploy_patches(host_ip, user, passwd):
        execute_cmd_without_stdout(
            host=host_ip, user=user, password=passwd,
            cmd='cd %s; python config.py cascading'
                % constant.PatchesConstant.PATCH_LUNCH_DIR)

        execute_cmd_without_stdout(
            host=host_ip, user=user, password=passwd,
            cmd='cd %s; python config.py prepare'
                % constant.PatchesConstant.PATCH_LUNCH_DIR)

        execute_cmd_without_stdout(
            host=host_ip, user=user, password=passwd,
            cmd='cd %s; python patches_tool.py'
                % constant.PatchesConstant.PATCH_LUNCH_DIR)

        return True

    def _enable_network_cross_fs_and_othercloud(self,cloud):
        cloud_id = cloud.cloud_id
        fs_vpn_eip = cloud.fs_vpn_eip
        fs_vpn_username = cloud.fs_vpn_username
        fs_vpn_password = cloud.fs_vpn_password
        fs_api_subnet_id = cloud.fs_api_subnet_id
        fs_api_vpn_ip = cloud.fs_api_vpn_ip
        fs_tunnel_subnet_id =cloud. fs_tunnel_subnet_id
        fs_tunnel_vpn_ip = cloud.fs_tunnel_vpn_ip 
        is_api_vpn = cloud.is_api_vpn
        cascaded_ip = cloud.cascaded_ip
        cascaded_user_name = cloud.cascaded_user_name
        cascaded_user_password = cloud.cascaded_user_password     
        
        vpn = VPN(public_ip=fs_vpn_eip,
              user=fs_vpn_username,
              pass_word=fs_vpn_password)
        
        self._copy_add_route_sh_to_fscascaded(cascaded_ip,cascaded_user_name,cascaded_user_password)
        
        # add vpn config for vcloud and aws
        for other_cloud_id in AwsCloudDataHandler().list_aws_clouds():
            other_cloud = AwsCloudDataHandler().get_aws_cloud(other_cloud_id)
            other_cloud_install_info = \
                cascaded_installer.get_aws_access_cloud_install_info(other_cloud_id)
            if not other_cloud.access:
                continue

            other_vpc_info = other_cloud_install_info["vpc"]
            other_vpn_info = other_cloud_install_info["vpn"]
            other_cascaded_info = other_cloud_install_info["cascaded"]
            other_vpn = VPN(public_ip=other_vpn_info["eip_public_ip"],
                            user=VpnConstant.AWS_VPN_ROOT,
                            pass_word=VpnConstant.AWS_VPN_ROOT_PWD)
            
            if is_api_vpn:
                LOG.info("add conn on api vpns...")
                api_conn_name = "%s-api-%s" % (cloud_id, other_cloud_id)
                vpn.add_tunnel(tunnel_name=api_conn_name,
                               left=fs_vpn_eip,
                               left_subnet=fs_api_subnet_id,
                               right=other_vpn_info["eip_public_ip"],
                               right_subnet=other_vpc_info["api_subnet_cidr"])
    
                other_vpn.add_tunnel(tunnel_name=api_conn_name,
                                     left=other_vpn_info["eip_public_ip"],
                                     left_subnet=other_vpc_info["api_subnet_cidr"],
                                     right=fs_vpn_eip,
                                     right_subnet=fs_api_subnet_id)

            LOG.info("add conn on tunnel vpns...")
            tunnel_conn_name = "%s-tunnel-%s" % (cloud.cloud_id, other_cloud_id)
            vpn.add_tunnel(tunnel_name=tunnel_conn_name,
                           left=fs_vpn_eip,
                           left_subnet=fs_tunnel_subnet_id,
                           right=other_vpn_info["eip_public_ip"],
                           right_subnet=other_vpc_info["tunnel_subnet_cidr"])

            other_vpn.add_tunnel(tunnel_name=tunnel_conn_name,
                                 left=other_vpn_info["eip_public_ip"],
                                 left_subnet=other_vpc_info["tunnel_subnet_cidr"],
                                 right=fs_vpn_eip,
                                 right_subnet=fs_tunnel_subnet_id)

            vpn.restart_ipsec_service()
            other_vpn.restart_ipsec_service()

            LOG.info("add route on openstack cascadeds...")
            execute_cmd_without_stdout(
                host=cascaded_ip,
                user=cascaded_user_name,
                password=cascaded_user_password,
                cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
                    % {"dir": constant.FsCascaded.REMOTE_SCRIPTS_DIR,
                       "script": constant.FsCascaded.ADD_ROUTE_SCRIPT,
                       "subnet": other_vpc_info["api_subnet_cidr"],
                       "gw": fs_api_vpn_ip})

            execute_cmd_without_stdout(
                host=other_cascaded_info["tunnel_ip"],
                user=constant.Cascaded.ROOT,
                password=constant.Cascaded.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(subnet)s %(gw)s'
                    % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                       "script": constant.Cascaded.ADD_API_ROUTE_SCRIPT,
                       "subnet": fs_api_subnet_id,
                       "gw": other_vpn_info["api_ip"]})
            
            #add security_group of vpn

            # add cloud-sg
            LOG.info("add aws sg...")
#             cascaded_installer.aws_access_cloud_add_security(
#                 region=cloud.get_region_id(),
#                 az=cloud.az,
#                 access_key=cloud.access_key,
#                 secret_key=cloud.secret_key,
#                 cidr="%s/32" % other_vpn_info["eip_public_ip"])

            cascaded_installer.aws_access_cloud_add_security(
                region=other_cloud.get_region_id(),
                az=cloud.az,
                access_key=other_cloud.access_key,
                secret_key=other_cloud.secret_key,
                cidr="%s/32" % fs_vpn_eip)

        return True

       
    @staticmethod
    def _enable_network_cross(cloud, cloud_install_info):
        cloud_id = cloud.cloud_id
        vpc_info = cloud_install_info["vpc"]
        vpn_info = cloud_install_info["vpn"]
        cascaded_info = cloud_install_info["cascaded"]
        vpn = VPN(public_ip=vpn_info["eip_public_ip"],
                  user=VpnConstant.AWS_VPN_ROOT,
                  pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

        for other_cloud_id in AwsCloudDataHandler().list_aws_clouds():
            if other_cloud_id == cloud_id:
                continue

            other_cloud = AwsCloudDataHandler().get_aws_cloud(other_cloud_id)
            other_cloud_install_info = \
                cascaded_installer.get_aws_access_cloud_install_info(other_cloud_id)
            if not other_cloud.access:
                continue

            other_vpc_info = other_cloud_install_info["vpc"]
            other_vpn_info = other_cloud_install_info["vpn"]
            other_cascaded_info = other_cloud_install_info["cascaded"]
            other_vpn = VPN(public_ip=other_vpn_info["eip_public_ip"],
                            user=VpnConstant.AWS_VPN_ROOT,
                            pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

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
            LOG.info("add aws sg...")
            cascaded_installer.aws_access_cloud_add_security(
                region=cloud.get_region_id(),
                az=cloud.az,
                access_key=cloud.access_key,
                secret_key=cloud.secret_key,
                cidr="%s/32" % other_vpn_info["eip_public_ip"])

            cascaded_installer.aws_access_cloud_add_security(
                region=other_cloud.get_region_id(),
                az=cloud.az,
                access_key=other_cloud.access_key,
                secret_key=other_cloud.secret_key,
                cidr="%s/32" % vpn_info["eip_public_ip"])

        return True

    @staticmethod
    def _config_storage(host_ip, user, password, cascading_domain,
                        cascaded_domain, install_info):
        # 1. create env file and config cinder on cascaded host
        for i in range(7):
            try:
                execute_cmd_without_stdout(
                    host=host_ip, user=user, password=password,
                    cmd='cd %(dir)s;'
                        'sh %(create_env_script)s %(cascading_domain)s '
                        '%(cascaded_domain)s;'
                        'sh %(conf_cinder_script)s '
                        '%(original_cascaded_domain)s '
                        '%(backup_cascaded_domain)s'
                        % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                           "create_env_script": constant.Cascaded.CREATE_ENV,
                           "cascading_domain": cascading_domain,
                           "cascaded_domain": cascaded_domain,
                           "conf_cinder_script":
                               constant.Cascaded.CONFIG_CINDER_SCRIPT,
                           "original_cascaded_domain": cascaded_domain,
                           "backup_cascaded_domain": cascaded_domain})
                break
            except Exception as e1:
                LOG.error("modify env file and config cinder "
                             "on cascaded host error: %s"
                             % e1.message)
                time.sleep(1)
                continue

        if "ceph_cluster" not in install_info.keys():
            return

        ceph_cluster = install_info["ceph_cluster"]
        # 2. config ceph nodes
        for i in range(7):
            try:
                execute_cmd_without_stdout(
                    host=ceph_cluster["deploy_ip"],
                    user=constant.CephConstant.USER,
                    password=constant.CephConstant.PWD,
                    cmd='/bin/bash %(ceph_install_script)s %(deploy_ip)s '
                        '%(node1_ip)s %(node2_ip)s %(node3_ip)s'
                        % {"ceph_install_script": constant.CephConstant.CEPH_INSTALL_SCRIPT,
                           "deploy_ip": ceph_cluster["deploy_ip"],
                           "node1_ip": ceph_cluster["node1_ip"],
                           "node2_ip": ceph_cluster["node2_ip"],
                           "node3_ip": ceph_cluster["node3_ip"]})
                break
            except SSHCommandFailure as e2:
                LOG.error("install ceph nodes error, error: %s" % e2.message)
                time.sleep(1)
                continue

        # 3. config cinder on cascaded host
        for i in range(7):
            try:
                execute_cmd_without_stdout(
                    host=host_ip,
                    user=user,
                    password=password,
                    cmd='cd %(dir)s; python %(config_backup_script)s '
                        '--domain=%(cascaded_domain)s '
                        '--backup_domain=%(backup_cascaded_domain)s '
                        '--host=%(host_ip)s '
                        '--backup_host=%(backup_host_ip)s'
                        % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                           "config_backup_script":
                               constant.Cascaded.CONFIG_CINDER_BACKUP_SCRIPT,
                           "cascaded_domain":
                               CloudManager._domain_to_region(cascaded_domain),
                           "backup_cascaded_domain":
                               CloudManager._domain_to_region(cascaded_domain),
                           "host_ip": ceph_cluster["node1_ip"],
                           "backup_host_ip": ceph_cluster["node1_ip"]})
                break
            except SSHCommandFailure as e3:
                LOG.error("config cinder backup error, error: %s"
                             % e3.message)
                time.sleep(1)

        return True

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
                                   aws_region=cloud.get_region_id(),
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

        self._create_ext_net(host_ip=self.cascading_api_ip,
                             user=constant.Cascading.ROOT,
                             passwd=constant.Cascading.ROOT_PWD,
                             alias=cloud.az_alias, vlan=vlan)

        self._create_ext_subnet(host_ip=self.cascading_api_ip,
                                user=constant.Cascading.ROOT,
                                passwd=constant.Cascading.ROOT_PWD,
                                alias=cloud.az_alias, eips=eips)

        proxy_num = cloud.cloud_proxy["proxy_num"]
        ext_net_name = "ext-%s-net" % cloud.az_alias
        self._update_proxy_params(host_ip=self.cascading_api_ip,
                                  user=constant.Cascading.ROOT,
                                  passwd=constant.Cascading.ROOT_PWD,
                                  proxy_num=proxy_num,
                                  ext_net_name=ext_net_name)

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

    @staticmethod
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
    def _update_l3_agent_conf(host_ip, user, passwd,
                              aws_region, access_key, secret_key,
                              subnet_cidr, interface_ip, interface_id,
                              used_ips):
        for i in range(3):
            try:
                execute_cmd_without_stdout(
                        host=host_ip, user=user, password=passwd,
                        cmd="cd %(dir)s; "
                            "sh %(script)s "
                            "%(aws_region)s %(access_key)s %(secret_key)s "
                            "%(subnet_cidr)s %(interface_ip)s "
                            "%(interface_id)s %(used_ips)s"
                            % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                               "script": constant.Cascaded.UPDATE_L3_AGENT_SCRIPT,
                               "aws_region": aws_region,
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
    def _domain_to_region(domain):
        domain_list = domain.split(".")
        region = domain_list[0] + "." + domain_list[1]
        return region

    @staticmethod
    def _disable_network_cross(cloud, install_info):
        # only disable other_cloud vpn
        for other_cloud_id in AwsCloudDataHandler().list_aws_clouds():
            if other_cloud_id == cloud.cloud_id:
                continue

            LOG.info("disable network cross, other_cloud_id=%s"
                        % other_cloud_id)
            other_cloud = AwsCloudDataHandler().get_aws_cloud(other_cloud_id)
            other_install_info = \
                cascaded_installer.get_aws_access_cloud_install_info(other_cloud_id)
            if other_cloud.access == "false":
                continue

            # delete api cross
            other_vpn_info = other_install_info["vpn"]
            other_vpn = VPN(public_ip=other_vpn_info["eip_public_ip"],
                            user=VpnConstant.AWS_VPN_ROOT,
                            pass_word=VpnConstant.AWS_VPN_ROOT_PWD)

            api_conn_name = "%s-api-%s" \
                            % (cloud.cloud_id, other_cloud.cloud_id)
            api_conn_name_alter = "%s-api-%s" \
                                  % (other_cloud.cloud_id, cloud.cloud_id)
            LOG.info("remove conn on api vpn...")

            other_vpn.remove_tunnel(api_conn_name)

            other_vpn.remove_tunnel(api_conn_name_alter)

            # delete tunnel cross
            tunnel_conn_name = "%s-tunnel-%s" \
                               % (cloud.cloud_id, other_cloud.cloud_id)
            tunnel_conn_name_alter = "%s-tunnel-%s" \
                                     % (other_cloud.cloud_id, cloud.cloud_id)
            LOG.info("remove conn on tunnel vpn...")

            other_vpn.remove_tunnel(tunnel_conn_name)

            other_vpn.remove_tunnel(tunnel_conn_name_alter)

            other_vpn.restart_ipsec_service()

            # remove cloud-sg
            LOG.info("remove aws sg...")
            cascaded_installer.aws_access_cloud_remove_security(
                cloud_id=other_cloud.cloud_id,
                region=other_cloud.get_region_id(),
                az=other_cloud.az,
                access_key=other_cloud.access_key,
                secret_key=other_cloud.secret_key,
                cidr="%s/32" % install_info["vpn"]["eip_public_ip"])

        return True

    @staticmethod
    def list_aws_cloud():
        return AwsCloudDataHandler().list_aws_clouds()

    @staticmethod
    def get_aws_cloud(cloud_id):
        return AwsCloudDataHandler().get_aws_cloud(cloud_id)

    def delete_aws_access_cloud(self, region_name, az, az_alias,
                                access_key, secret_key):
        cloud_id = "@".join([access_key, region_name, az])
        cloud = AwsCloudDataHandler().get_aws_cloud(cloud_id=cloud_id)
        cloud_install_info = \
            cascaded_installer.get_aws_access_cloud_install_info(cloud_id)

        if cloud is None:
            LOG.error("no such cloud, cloud_id=%s" % cloud_id)
            return True

        if cloud_install_info:
            if cloud.driver_type == "agentless":
                LOG.info("remove hyper node...")
                hynode_manager = HyperNodeManager(
                        access_key_id=cloud.access_key,
                        secret_key_id=cloud.secret_key,
                        region=cloud.region,
                        vpc_id=cloud_install_info["vpc"]["vpc_id"])
                hynode_manager.start_remove_all()

            LOG.info("remove aws cascaded...")
            cascaded_installer.aws_access_cloud_uninstall(
                    cloud_id=cloud_id,
                    region=cloud.get_region_id(),
                    az=cloud.az,
                    access_key=cloud.access_key,
                    secret_key=cloud.secret_key)

        # config cascading
        try:
            execute_cmd_without_stdout(
                host=self.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_AGGREGATE_SCRIPT,
                       "cascaded_domain": cloud.cascaded_domain})
        except Exception as e:
            LOG.error("remove aggregate error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(
                host=self.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_CINDER_SERVICE_SCRIPT,
                       "cascaded_domain": cloud.cascaded_domain})
        except Exception as e:
            LOG.error("remove cinder service error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(
                host=self.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
                       "cascaded_domain": cloud.cascaded_domain})

            execute_cmd_without_stdout(
                host=self.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(proxy_host)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script":
                           constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
                       "proxy_host": cloud.cloud_proxy["id"]})

        except Exception as e:
            LOG.error("remove neutron agent error, error: %s" % e.message)

        try:
            execute_cmd_without_stdout(
                host=self.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.RemoveConstant.REMOVE_KEYSTONE_SCRIPT,
                       "cascaded_domain": cloud.cascaded_domain})
        except SSHCommandFailure:
            LOG.error("remove keystone endpoint error.")

        try:
            execute_cmd_without_stdout(
                host=self.cascading_api_ip,
                user=constant.Cascading.ROOT,
                password=constant.Cascading.ROOT_PWD,
                cmd='cd %(dir)s; '
                    'sh %(script)s %(proxy_host_name)s %(proxy_num)s'
                    % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
                       "script": constant.RemoveConstant.REMOVE_PROXY_SCRIPT,
                       "proxy_host_name": cloud.cloud_proxy["id"],
                       "proxy_num": cloud.cloud_proxy["proxy_num"]})
        except SSHCommandFailure:
            LOG.error("remove proxy error.")

        address = "/%(cascaded_domain)s/%(cascaded_ip)s" \
                  % {"cascaded_domain": cloud.cascaded_domain,
                     "cascaded_ip": cloud_install_info["cascaded"]["api_ip"]}

        try:
            execute_cmd_without_stdout(
                host=self.cascading_api_ip,
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
        vpn_conn_name = cloud.get_vpn_conn_name()
        try:
            local_vpn = VPN(self.local_vpn_ip,
                            constant.VpnConstant.VPN_ROOT,
                            constant.VpnConstant.VPN_ROOT_PWD)
            local_vpn.remove_tunnel(vpn_conn_name["api_conn_name"])
            local_vpn.remove_tunnel(vpn_conn_name["tunnel_conn_name"])
        except SSHCommandFailure:
            LOG.error("remove conn error.")

        # release subnet
        subnet_pair = {
            'api_subnet': cloud_install_info["vpc"]["api_subnet_cidr"],
            'tunnel_subnet': cloud_install_info["vpc"]["tunnel_subnet_cidr"]}
        SubnetManager().release_subnet_pair(subnet_pair)

        try:
            self._disable_network_cross(
                cloud=cloud, install_info=cloud_install_info)
        except Exception:
            LOG.error("disable network cross error.")

        AwsCloudDataHandler().delete_aws_cloud(cloud_id)

        LOG.info("delete cloud success. cloud_id = %s" % cloud_id)

        return True
    
    # def delete_fs_access_cloud(self, azName, dc,suffix,is_api_vpn,fs_vpn_eip,fs_vpn_username,
    #                             fs_vpn_password,cascaded_ip,fs_gateway_ip):
    #     cloud_id = "@".join([azName, dc, suffix])
    #     cloud_region = ".".join([azName, dc])
    #     cloud = FsCloudDataHandler().get_fs_cloud(cloud_id=cloud_id)
    #     cloud_domain = ".".join([azName, dc])
    #
    #     # config local_vpn
    #     vpn_conn_name = cloud.get_vpn_conn_name()
    #     try:
    #         LOG.info("remove conn on vpn for cascading...")
    #         local_vpn = VPN(self.local_vpn_ip,
    #                        constant.VpnConstant.VPN_ROOT,
    #                        constant.VpnConstant.VPN_ROOT_PWD)
    #         if is_api_vpn:
    #             local_vpn.remove_tunnel(vpn_conn_name["api_conn_name"])
    #         local_vpn.remove_tunnel(vpn_conn_name["tunnel_conn_name"])
    #
    #
    #         LOG.info("remove conn on vpn for fscloud...")
    #         fs_vpn = VPN(fs_vpn_eip,fs_vpn_username,fs_vpn_password)
    #         if is_api_vpn:
    #             fs_vpn.remove_tunnel(vpn_conn_name["api_conn_name"])
    #         fs_vpn.remove_tunnel(vpn_conn_name["tunnel_conn_name"])
    #
    #     except SSHCommandFailure:
    #         LOG.error("remove conn error.")
    #
    #     LOG.info("remove aggregate ...")
    #     try:
    #         execute_cmd_without_stdout(
    #             host=self.cascading_api_ip,
    #             user=constant.Cascading.ROOT,
    #             password=constant.Cascading.ROOT_PWD,
    #             cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
    #                 % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
    #                    "script":
    #                        constant.RemoveConstant.REMOVE_AGGREGATE_SCRIPT,
    #                    "cascaded_domain": cloud_domain})
    #     except Exception as e:
    #         LOG.error("remove aggregate error, error: %s" % e.message)
    #
    #     LOG.info("remove cinder service ...")
    #     try:
    #         execute_cmd_without_stdout(
    #             host=self.cascading_api_ip,
    #             user=constant.Cascading.ROOT,
    #             password=constant.Cascading.ROOT_PWD,
    #             cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
    #                 % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
    #                    "script":
    #                        constant.RemoveConstant.REMOVE_CINDER_SERVICE_SCRIPT,
    #                    "cascaded_domain": cloud_domain})
    #     except Exception as e:
    #         LOG.error("remove cinder service error, error: %s" % e.message)
    #
    #     LOG.info("remove neutron agent ...")
    #     try:
    #         execute_cmd_without_stdout(
    #             host=self.cascading_api_ip,
    #             user=constant.Cascading.ROOT,
    #             password=constant.Cascading.ROOT_PWD,
    #             cmd='cd %(dir)s; sh %(script)s %(cascaded_domain)s'
    #                 % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
    #                    "script":
    #                        constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
    #                    "cascaded_domain":cloud_domain})
    #
    #         execute_cmd_without_stdout(
    #             host=self.cascading_api_ip,
    #             user=constant.Cascading.ROOT,
    #             password=constant.Cascading.ROOT_PWD,
    #             cmd='cd %(dir)s; sh %(script)s %(proxy_host)s'
    #                 % {"dir": constant.RemoveConstant.REMOTE_SCRIPTS_DIR,
    #                    "script":
    #                        constant.RemoveConstant.REMOVE_NEUTRON_AGENT_SCRIPT,
    #                    "proxy_host": cloud.cloud_proxy["id"]})
    #
    #     except Exception as e:
    #         LOG.error("remove neutron agent error, error: %s" % e.message)
    #
    #
    #     # LOG.info("unregister fscloud...")
    #     # fs_gateway_register.unregister_availability_zone(azName, dc, suffix, cascaded_ip,
    #     #                          cloud.cloud_proxy["id"], cloud.cloud_proxy["proxy_num"], fs_gateway_ip)
    #
    #     try:
    #         LOG.info("begin delete associate map fscloud...")
    #         associate_usr_id =  cloud.associate_user_id
    #         associate_admin_id = cloud.associate_admin_id
    #         associate_service_id = cloud.associate_service_id
    #         LOG.debug('the associate_usr_id=%s,associate_admin_id=%s,associate_service_id=%s',
    #                      associate_usr_id,associate_admin_id, associate_service_id)
    #
    #         fsclient.associations.set_name('project')
    #         fsclient.associations.delete(associate_admin_id)
    #         fsclient.associations.delete(associate_service_id)
    #         fsclient.users.delete(associate_usr_id)
    #     except Exception as e:
    #         LOG.warning("delete associate map failed,please check it,error:%s" % e.message)
    #
    #     self._update_fsgateway_config( host_ip=self.cascading_api_ip,
    #             user=constant.Cascading.ROOT,
    #             passwd=constant.Cascading.ROOT_PWD,
    #             action ='delete', region=cloud_region)
    #
    #     FsCloudDataHandler().delete_fs_cloud(cloud_id)
    #     return True
  
    @staticmethod
    def _get_domain_type(domain):
        domain_list = domain.split(".")
        domain_type = domain_list[1].split("--")[1]
        return domain_type

    @staticmethod
    def get_cloud_user_pwd(cloud_id):
        type = CloudManager._get_domain_type(cloud_id)
        if type == "vcloud":
            return CloudManager.get_vcloud_cloud(
                cloud_id), VcloudConstant.ROOT, VcloudConstant.ROOT_PWD
        elif type == "aws":
            return CloudManager.get_aws_cloud(
                cloud_id), AwsConstant.ROOT, AwsConstant.ROOT_PWD
        elif type == "fusionsphere":
            return CloudManager.get_fusionsphere_cloud(
                cloud_id), FusionsphereConstant.ROOT, FusionsphereConstant.ROOT_PWD
        else:
            raise Exception("cloud %s type error" % cloud_id)

    @staticmethod
    def _ceph_config(cloud_ip, cloud_user, cloud_pwd, region, backup_region,
                     ceph_ip, backup_ceph_ip):
        # config in cloud, backup in backup_region
        for i in range(7):
            try:
                execute_cmd_without_stdout(
                    host=cloud_ip,
                    user=cloud_user,
                    password=cloud_pwd,
                    cmd='cd %(dir)s; python %(config_backup_script)s '
                        '--domain=%(cascaded_domain)s '
                        '--backup_domain=%(backup_cascaded_domain)s '
                        '--host=%(host_ip)s '
                        '--backup_host=%(backup_host_ip)s'
                        % {"dir": constant.Cascaded.REMOTE_SCRIPTS_DIR,
                           "config_backup_script":
                               constant.Cascaded.CONFIG_CINDER_BACKUP_SCRIPT,
                           "cascaded_domain": region,
                           "backup_cascaded_domain": backup_region,
                           "host_ip": ceph_ip,
                           "backup_host_ip": backup_ceph_ip})
                return True
            except SSHCommandFailure as e3:
                LOG.error("config cinder backup error, error: %s"
                             % e3.message)
                time.sleep(1)
        return False

    @staticmethod
    def backup_across_az(domain_1, domain_2):
        LOG.info("volume backup: %s <-> %s" % (domain_1, domain_2))
        region_1 = CloudManager._domain_to_region(domain_1)
        cloud_1, cloud1_user, cloud1_pwd = CloudManager.get_cloud_user_pwd(
            domain_1)
        cloud1_ceph_ip = cloud_1.ceph_vm["ceph_node1_vm_ip"]
        cloud1_ip = cloud_1.cascaded_openstack["api_ip"]

        if domain_1 == domain_2:
            # config in cloud1, backup in cloud2
            CloudManager._ceph_config(cloud_ip=cloud1_ip,
                                      cloud_user=cloud1_user,
                                      cloud_pwd=cloud1_pwd,
                                      region=region_1,
                                      backup_region=region_1,
                                      ceph_ip=cloud1_ceph_ip,
                                      backup_ceph_ip=cloud1_ceph_ip)
            return

        region_2 = CloudManager._domain_to_region(domain_2)
        cloud_2, cloud2_user, cloud2_pwd = CloudManager.get_cloud_user_pwd(
            domain_2)
        cloud2_ceph_ip = cloud_2.ceph_vm["ceph_node1_vm_ip"]
        cloud2_ip = cloud_2.cascaded_openstack["api_ip"]

        # config in cloud1, backup in cloud2
        result_1 = CloudManager._ceph_config(cloud_ip=cloud1_ip,
                                             cloud_user=cloud1_user,
                                             cloud_pwd=cloud1_pwd,
                                             region=region_1,
                                             backup_region=region_2,
                                             ceph_ip=cloud1_ceph_ip,
                                             backup_ceph_ip=cloud2_ceph_ip)
        # config in cloud2, backup in cloud1
        result_2 = CloudManager._ceph_config(cloud_ip=cloud2_ip,
                                             cloud_user=cloud2_user,
                                             cloud_pwd=cloud2_pwd,
                                             region=region_2,
                                             backup_region=region_1,
                                             ceph_ip=cloud2_ceph_ip,
                                             backup_ceph_ip=cloud1_ceph_ip)

        # cross az failed
        if not result_1 or not result_2:
            # config in cloud1, backup in cloud1
            CloudManager._ceph_config(cloud_ip=cloud1_ip,
                                      cloud_user=cloud1_user,
                                      cloud_pwd=cloud1_pwd,
                                      region=region_1,
                                      backup_region=region_1,
                                      ceph_ip=cloud1_ceph_ip,
                                      backup_ceph_ip=cloud1_ceph_ip)

            # config in cloud2, backup in cloud2
            CloudManager._ceph_config(cloud_ip=cloud2_ip,
                                      cloud_user=cloud2_user,
                                      cloud_pwd=cloud2_pwd,
                                      region=region_2,
                                      backup_region=region_2,
                                      ceph_ip=cloud2_ceph_ip,
                                      backup_ceph_ip=cloud2_ceph_ip)
