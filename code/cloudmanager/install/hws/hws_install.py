
import time
import socket
from heat.openstack.common import log as logging

import heat.engine.resources.cloudmanager.util.conf_util as conf_util
from heat.engine.resources.cloudmanager.exception import *
from heat.engine.resources.cloudmanager.environmentinfo import *
import heat.engine.resources.cloudmanager.proxy_manager as proxy_manager
import heat.engine.resources.cloudmanager.constant as constant

from hws_util import *
from hws_cloud_info_persist import *
import pdb

LOG = logging.getLogger(__name__)

SUBNET_GATEWAY_TAIL_IP = "1"
VPN_TAIL_IP = "254"
CASCADED_TAIL_IP = "4"
ROOT_VOLUME_TYPE = 'SATA'

class HwsCascadedInstaller(object):
    def __init__(self, cloud_params):
        self._init_params(cloud_params)
        self._read_env()
        start_hws_gateway(self.cascading_api_ip, constant.Cascading.ROOT,
                           constant.Cascading.ROOT_PWD)
        self._read_install_info()

    def _init_params(self, cloud_params):
        self.cloud_info = cloud_params
        self.cloud_id = "@".join(["HWS", cloud_params['azname']])
        self.cascaded_image = cloud_params["cascaded_info"]["image"]
        self.cascaded_flavor = cloud_params["cascaded_info"]["flavor"]
        self.vpn_image = cloud_params["vpn_info"]["image"]
        self.vpn_flavor = cloud_params["vpn_info"]["flavor"]
        self.installer = HwsInstaller(cloud_params["project_info"])
        self.availability_zone = cloud_params["project_info"]["availability_zone"]

        network = cloud_params["network"]
        self.vpc_cidr = network["vpc_cidr"]
        self.external_api_cidr = network["external_api_cidr"]
        self.tunnel_bearing_cidr = network["tunnel_bearing_cidr"]
        self.internal_base_cidr = network["internal_base_cidr"]
        self.debug_cidr = network["debug_cidr"]

        self.install_data_handler = \
            HwsCloudInfoPersist(constant.HwsConstant.INSTALL_INFO_FILE, self.cloud_id)
        self.cloud_info_handler = \
            HwsCloudInfoPersist(constant.HwsConstant.CLOUD_INFO_FILE, self.cloud_id)

    def _read_env(self):
        try:
            env_info = conf_util.read_conf(constant.Cascading.ENV_FILE)
            self.env = env_info["env"]
            self.cascading_api_ip = env_info["cascading_api_ip"]
            self.cascading_domain = env_info["cascading_domain"]
            self.cascading_vpn_ip = env_info["local_vpn_ip"]
            self.cascading_vpn_public_gw = env_info["local_vpn_public_gw"]
            self.cascading_eip = env_info["cascading_eip"]
            self.cascading_api_subnet = env_info["local_api_subnet"]
            self.cascading_vpn_api_ip = env_info["local_vpn_api_ip"]
            self.cascading_tunnel_subnet = env_info["local_tunnel_subnet"]
            self.cascading_vpn_tunnel_ip = env_info["local_vpn_tunnel_ip"]
            self.existed_cascaded = env_info["existed_cascaded"]
        except IOError as e:
            error = "read file = %s error" % constant.Cascading.ENV_FILE
            LOG.error(e)
            raise ReadEnvironmentInfoFailure(error = error)
        except KeyError as e:
            error = "read key = %s error in file = %s" % (e.message, _environment_conf)
            LOG.error(error)
            raise ReadEnvironmentInfoFailure(error = error)

    def _create_vpc(self):
        name = self.cloud_info["azname"]+"_vpc"
        cidr = self.vpc_cidr

        if self.vpc_id is None:
            self.vpc_id = self.installer.create_vpc(name, cidr)
        try:
            if self.security_group_id is None:
                security_group_id = self.installer.get_security_group(self.vpc_id)
                self.installer.create_security_group_rule(
                    security_group_id, "ingress", "IPv4")
                self.security_group_id = security_group_id
        finally:
            self.install_data_handler.write_vpc_info(self.vpc_id, name, cidr, self.security_group_id)

    def _delete_vpc(self):
        if self.vpc_id:
            self.installer.delete_vpc(self.vpc_id)

    def _create_subnet(self):
        az = self.availability_zone
        self.external_api_gateway = self._alloc_gateway_ip(self.external_api_cidr)
        tunnel_bearing_gateway = self._alloc_gateway_ip(self.tunnel_bearing_cidr)
        internal_base_gateway = self._alloc_gateway_ip(self.internal_base_cidr)
        debug_gateway = self._alloc_gateway_ip(self.debug_cidr)

        external_api_info = {
                "id": None,
                "cidr": None
            }
        tunnel_bearing_info = {
                "id": None,
                "cidr": None
            }
        internal_base_info = {
                "id": None,
                "cidr": None
            }
        debug_info = {
                "id": None,
                "cidr": None
            }
        try:
            if self.external_api_id is None:
                self.external_api_id = self.installer.create_subnet("external_api",
                                    self.external_api_cidr, az, self.external_api_gateway,
                                    self.vpc_id)
            if self.tunnel_bearing_id is None:
                self.tunnel_bearing_id = self.installer.create_subnet("tunnel_bearing",
                                  self.tunnel_bearing_cidr, az, tunnel_bearing_gateway,
                                  self.vpc_id)
            if self.internal_base_id is None:
                self.internal_base_id = self.installer.create_subnet("internal_base",
                                  self.internal_base_cidr, az, internal_base_gateway,
                                  self.vpc_id)
            if self.debug_id is None:
                self.debug_id = self.installer.create_subnet("debug",
                                  self.debug_cidr, az, debug_gateway,
                                  self.vpc_id)

            external_api_info = {
                "id": self.external_api_id,
                "cidr": self.external_api_cidr
            }
            tunnel_bearing_info = {
                "id": self.tunnel_bearing_id,
                "cidr": self.tunnel_bearing_cidr
            }
            internal_base_info = {
                "id": self.internal_base_id,
                "cidr": self.internal_base_cidr
            }
            debug_info = {
                "id": self.debug_id,
                "cidr": self.debug_cidr
            }
        finally:
            self.install_data_handler.write_subnets_info(external_api_info, tunnel_bearing_info, internal_base_info, debug_info)

    def _delete_subnet(self):
        if self.external_api_id:
            self.installer.delete_subnet(self.vpc_id, self.external_api_id)
        if self.tunnel_bearing_id:
            self.installer.delete_subnet(self.vpc_id, self.tunnel_bearing_id)
        if self.internal_base_id:
            self.installer.delete_subnet(self.vpc_id, self.internal_base_id)
        if self.debug_id:
            self.installer.delete_subnet(self.vpc_id, self.debug_id)

    @staticmethod
    def _alloc_gateway_ip(cidr):
        ip_list = cidr.split(".")
        gateway_ip = ".".join([ip_list[0], ip_list[1], ip_list[2], SUBNET_GATEWAY_TAIL_IP])
        return gateway_ip

    @staticmethod
    def _alloc_vpn_ip(cidr):
        ip_list = cidr.split(".")
        vpn_ip = ".".join([ip_list[0], ip_list[1], ip_list[2], VPN_TAIL_IP])
        return vpn_ip

    @staticmethod
    def _alloc_cascaded_ip(cidr, tail_ip):
        ip_list = cidr.split(".")
        cascaded_ip = ".".join([ip_list[0], ip_list[1], ip_list[2], tail_ip])
        return cascaded_ip
    
    def _alloc_vpn_public_ip(self):
        if self.vpn_public_ip_id is None:
            public_ip_name = self.cloud_info["azname"]+"_vpn_public_ip"
            result = self.installer.alloc_public_ip(public_ip_name)
            self.vpn_public_ip = result["public_ip_address"]
            self.vpn_public_ip_id = result["id"]

            self.install_data_handler.write_public_ip_info(
                self.vpn_public_ip,
                self.vpn_public_ip_id
                )

    def _alloc_cascaded_public_ip(self):
        if self.cascaded_public_ip_id is None:
            public_ip_name = self.cloud_info["azname"]+"_cascaded_public_ip"
            result = self.installer.alloc_public_ip(public_ip_name)
            self.cascaded_public_ip = result["public_ip_address"]
            self.cascaded_public_ip_id = result["id"]
            self.install_data_handler.write_public_ip_info(
                self.vpn_public_ip,
                self.vpn_public_ip_id,
                self.cascaded_public_ip,
                self.cascaded_public_ip_id
                )

    def _release_public_ip(self):
        self.installer.release_public_ip(self.vpn_public_ip_id)
        self.installer.release_public_ip(self.cascaded_public_ip_id)

    def cloud_preinstall(self):
        pass
    def cloud_preuninstall(self):
        pass

    def _install_network(self):
        self._create_vpc()
        self._create_subnet()

    def _uninstall_network(self):
        self._delete_subnet()
        self._delete_vpc()

    def cloud_postinstall(self):
        pass

    def cloud_postuninstall(self):
        #pdb.set_trace()
        self.install_data_handler.delete_cloud_info()
        self.cloud_info_handler.delete_cloud_info()

    def cloud_install(self):
        self._cloud_install()

    def _cloud_install(self):
        self._install_proxy()
        self._install_network()
        if self.cloud_info["vpn_info"]["exist"] == "true":
            self._read_exist_vpn_info()
        else:
            self._install_vpn()
        self._install_cascaded()

    def _read_exist_vpn_info(self):
        vpn_info = self.cloud_info["vpn_info"]
        self.vpn_public_ip = vpn_info["public_ip"],
        self.vpn_external_api_ip = vpn_info["external_api_ip"],
        self.vpn_tunnel_bearing_ip = vpn_info["tunnel_bearing_ip"]

    def cloud_uninstall(self):
        self._cloud_uninstall()
        pass

    def _cloud_uninstall(self):
        self.uninstall_cascaded()
        self.uninstall_vpn()
        if self.delete_cascaded_job_id:
            self.installer.block_until_delete_resource_success(self.delete_cascaded_job_id)
        if self.delete_vpn_job_id:
            self.installer.block_until_delete_resource_success(self.delete_vpn_job_id)
        self._uninstall_network()

    def _install_proxy(self):
        if self.proxy_info is None:
            self.proxy_info = proxy_manager.distribute_proxy()
        self.install_data_handler.write_proxy(self.proxy_info)

    def _install_cascaded(self):
        self.cascaded_internal_base_ip = self._alloc_cascaded_ip(self.internal_base_cidr, "12")
        self.cascaded_tunnel_bearing_ip = self._alloc_cascaded_ip(self.tunnel_bearing_cidr, "4")
        self.cascaded_external_api_ip = self._alloc_cascaded_ip(self.external_api_cidr, "4")
        self.cascaded_debug_ip = self._alloc_cascaded_ip(self.debug_cidr, "4")

        nics = [{"subnet_id": self.debug_id,
                 "ip_address": self.cascaded_debug_ip}]
        security_groups = [self.security_group_id]
        server_name = self.cloud_info["azname"]+"_cascaded"
        try:
            if self.cascaded_server_id is None:
                self.cascaded_server_job_id = self.installer.create_vm(self.cascaded_image,
                                      self.cascaded_flavor,
                                      server_name, self.vpc_id,
                                      nics,ROOT_VOLUME_TYPE,
                                      self.availability_zone,
                                      adminPass = constant.HwsConstant.ROOT_PWD,
                                      security_groups = security_groups)
                self.cascaded_server_id = self.installer.block_until_create_vm_success(self.cascaded_server_job_id)
            self._create_cascaded_nics()
            self._modify_cascaded_external_api()
        finally:
            self.install_data_handler.write_cascaded_info(
                    self.cascaded_server_id,self.cascaded_public_ip,
                    self.cascaded_external_api_ip,self.cascaded_tunnel_bearing_ip,
                    self.tunnel_bearing_nic_id, self.external_api_nic_id,
                    self.internal_base_nic_id, self.port_id_bind_public_ip)

            if self.vpn_server_id is None:
                self.vpn_server_id = self.installer.block_until_create_vm_success(self.vpn_server_job_id)

            self.unbound_vpn_ip_mac()

            self.install_data_handler.write_vpn(
                    self.vpn_server_id, self.vpn_public_ip,
                    self.vpn_external_api_ip, self.vpn_tunnel_bearing_ip
            )
        LOG.info("install cascaded success.")

    def unbound_vpn_ip_mac(self):
        nics = self.installer.get_all_nics(self.vpn_server_id)
        for nic in nics:
            port_id = nic["port_id"]
            mac_address = nic["mac_addr"]
            self.installer.unbound_ip_mac(port_id, mac_address)

    def _create_cascaded_nics(self):
        ##nic should add one by one to maintain right sequence
        security_groups = [{"id":self.security_group_id}]
        if self.internal_base_nic_id is None:
            job_id = self.installer.add_nics(self.cascaded_server_id, self.internal_base_id,
                                security_groups, self.cascaded_internal_base_ip)
            self.internal_base_nic_id = self.installer.block_until_create_nic_success(job_id)
        if self.external_api_nic_id is None:
            job_id = self.installer.add_nics(self.cascaded_server_id, self.external_api_id,
                                security_groups, self.cascaded_external_api_ip)
            self.external_api_nic_id = self.installer.block_until_create_nic_success(job_id)
        if self.tunnel_bearing_nic_id is None:
            job_id = self.installer.add_nics(self.cascaded_server_id, self.tunnel_bearing_id,
                                security_groups, self.cascaded_tunnel_bearing_ip)
            self.tunnel_bearing_nic_id = self.installer.block_until_create_nic_success(job_id)
        if self.port_id_bind_public_ip is None:
            #pdb.set_trace()
            external_api_port_id = self.installer.get_external_api_port_id(
                self.cascaded_server_id, self.external_api_nic_id)
            self._alloc_cascaded_public_ip()
            self.installer.bind_public_ip(self.cascaded_public_ip_id, external_api_port_id)
            self.port_id_bind_public_ip = external_api_port_id
            #pdb.set_trace()
            self.installer.reboot(self.cascaded_server_id, "SOFT")

    def _modify_cascaded_external_api(self):
        #ssh to vpn, then ssh to cascaded through vpn tunnel_bearing_ip
        self.cascaded_domain = self._distribute_cloud_domain(
                     self.cloud_info["project_info"]['region'], self.cloud_info['azname'], "--hws"),
        modify_cascaded_api_domain_cmd = 'cd %(dir)s; ' \
                    'source /root/adminrc; ' \
                    'python %(script)s '\
                    '%(cascading_domain)s %(cascading_api_ip)s '\
                    '%(cascaded_domain)s %(cascaded_ip)s '\
                    '%(gateway)s'\
                    % {"dir": constant.Cascaded.REMOTE_HWS_SCRIPTS_DIR,
                       "script":constant.Cascaded.MODIFY_CASCADED_SCRIPT_PY,
                       "cascading_domain": self.cascading_domain,
                       "cascading_api_ip": self.cascading_api_ip,
                       "cascaded_domain":  self.cascaded_domain,
                       "cascaded_ip": self.cascaded_external_api_ip,
                       "gateway": self.external_api_gateway}
        #pdb.set_trace()
        for i in range(180):
            try:
                execute_cmd_without_stdout(
                    host= self.vpn_public_ip,
                    user=constant.VpnConstant.VPN_ROOT,
                    password=constant.VpnConstant.VPN_ROOT_PWD,
                    cmd='cd %(dir)s; python %(script)s '
                        '%(cascaded_tunnel_ip)s %(user)s %(passwd)s \'%(cmd)s\''
                    % {"dir": constant.VpnConstant.REMOTE_ROUTE_SCRIPTS_DIR,
                       "script": constant.VpnConstant.MODIFY_CASCADED_API_SCRIPT,
                       "cascaded_tunnel_ip": self.cascaded_tunnel_bearing_ip,
                       "user": constant.HwsConstant.ROOT,
                       "passwd": constant.HwsConstant.ROOT_PWD,
                       "cmd": modify_cascaded_api_domain_cmd})
                return True
            except Exception as e:
                if i == 120:
                    #wait cascaded vm to reboot ok
                    self.installer.reboot(self.cascaded_server_id, "SOFT")
                    LOG.error("can not connect to cascaded tunnel ip, error: %s, reboot it" % e.message)
                    return False
                time.sleep(1)

    def uninstall_cascaded(self):
        self._uninstall_cascaded()

    def _uninstall_cascaded(self):
        if self.cascaded_server_id is None:
            self.delete_cascaded_job_id = None
            return
        servers = [self.cascaded_server_id]
        self.delete_cascaded_job_id = self.installer.delete_vm(servers, True, True)

    def _install_vpn(self):
        self._alloc_vpn_public_ip()
        publicip = dict()
        publicip["id"] = self.vpn_public_ip_id
        self.vpn_external_api_ip = self._alloc_vpn_ip(self.external_api_cidr)
        self.vpn_tunnel_bearing_ip = self._alloc_vpn_ip(self.tunnel_bearing_cidr)

        nics = [{"subnet_id": self.external_api_id,
                "ip_address": self.vpn_external_api_ip},
                {"subnet_id": self.tunnel_bearing_id,
                "ip_address": self.vpn_tunnel_bearing_ip}]
        server_name = self.cloud_info["azname"]+"_vpn"
        if self.vpn_server_id is None:
            self.vpn_server_job_id = self.installer.create_vm(
                self.vpn_image,
                self.vpn_flavor, server_name,
                self.vpc_id, nics,
                ROOT_VOLUME_TYPE,
                self.availability_zone,
                public_ip_id=self.vpn_public_ip_id,
                adminPass=constant.VpnConstant.VPN_ROOT_PWD,
                security_groups=[self.security_group_id])

    def uninstall_vpn(self):
        self._uninstall_vpn()

    def _uninstall_vpn(self):
        if self.vpn_server_id is None:
            self.delete_vpn_job_id = None
            return
        servers = [self.vpn_server_id]
        self.delete_vpn_job_id = self.installer.delete_vm(servers, True, True)

    def package_cloud_info(self):
        return self.package_hws_cloud_info()

    def _distribute_cloud_domain(self, region_name, azname, az_tag):
        domain_list = self.cascading_domain.split(".")
        domainpostfix = ".".join([domain_list[2], domain_list[3]])
        l_region_name = region_name.lower()
        cloud_cascaded_domain = ".".join(
                [azname, l_region_name + az_tag, domainpostfix])
        self.cascaded_aggregate = ".".join([azname, l_region_name + az_tag])
        return cloud_cascaded_domain

    def package_hws_cloud_info(self):

        cascaded_vpn_info = {
            "public_ip": self.vpn_public_ip,
            "external_api_ip": self.vpn_external_api_ip,
            "tunnel_bearing_ip": self.vpn_tunnel_bearing_ip
        }

        cascaded_info = {
            "public_ip": self.cascaded_public_ip,
            "external_api_ip": self.cascaded_external_api_ip,
            "tunnel_bearing_ip": self.cascaded_tunnel_bearing_ip,
            "internal_base_ip": self.cascaded_internal_base_ip,
            "domain": self._distribute_cloud_domain(
                     self.cloud_info["project_info"]['region'], self.cloud_info['azname'], "--hws"),
            "aggregate": self.cascaded_aggregate
        }

        cascaded_subnets_info = {
            "vpc_id": self.vpc_id,
            "security_group_id": self.security_group_id,
            "tunnel_bearing_id": self.tunnel_bearing_id,
            "internal_base_id": self.internal_base_id,
            "external_api": self.external_api_cidr,
            "external_api_gateway_ip": self.external_api_gateway,
            "tunnel_bearing": self.tunnel_bearing_cidr,
            "internal_base": self.internal_base_cidr,
            "debug": self.debug_cidr
        }

        cascading_info = {
            "external_api_ip": self.cascading_api_ip,
            "domain": self.cascading_domain

        }

        cascading_vpn_info = {
            "public_ip": self.cascading_vpn_public_gw,
            "external_api_ip": self.cascading_vpn_api_ip,
            "tunnel_bearing_ip": self.cascading_vpn_tunnel_ip
        }

        cascading_subnets_info = {
            "external_api": self.cascading_api_subnet,
            "tunnel_bearing": self.cascading_tunnel_subnet
        }

        vpn_conn_name = {
            "api_conn_name": self.cloud_id + '-api',
            "tunnel_conn_name": self.cloud_id + '-tunnel'
        }
        #pdb.set_trace()
        info = {"cloud_id": self.cloud_id,
                "access": self.cloud_info["access"],
                "cascaded_vpn_info":cascaded_vpn_info,
                "cascading_vpn_info":cascading_vpn_info,
                "cascaded_info": cascaded_info,
                "cascading_info":cascading_info,
                "cascaded_subnets_info": cascaded_subnets_info,
                "cascading_subnets_info": cascading_subnets_info,
                "vpn_conn_name": vpn_conn_name,
                "proxy_info": self.proxy_info
                }

        self.cloud_info_handler.write_cloud_info(info)
        return info

    def _read_install_info(self):
        self.vpc_id = None
        self.internal_base_id = None
        self.debug_id = None
        self.external_api_id = None
        self.tunnel_bearing_id = None
        self.vpn_server_id = None
        self.cascaded_server_id = None
        self.cascaded_public_ip = None
        self.cascaded_public_ip_id = None
        self.vpn_public_ip_id = None
        self.tunnel_bearing_nic_id = None
        self.external_api_nic_id = None
        self.internal_base_nic_id = None
        self.port_id_bind_public_ip = None
        self.security_group_id = None
        self.proxy_info = None
        cloud_info = self.install_data_handler.read_cloud_info()

        if cloud_info is None:
            return
        if "proxy_info" in cloud_info.keys():
            self.proxy_info = cloud_info["proxy_info"]

        if "vpc" in cloud_info.keys():
            self.vpc_id = cloud_info["vpc"]["id"]
            self.security_group_id = cloud_info["vpc"]["security_group_id"]
        if "subnets" in cloud_info.keys():
            subnets = cloud_info["subnets"]
            self.internal_base_id = subnets["internal_base"]["id"]
            self.debug_id = subnets["debug"]["id"]
            self.external_api_id = subnets["external_api"]["id"]
            self.tunnel_bearing_id = subnets["tunnel_bearing"]["id"]
        if "vpn" in cloud_info.keys():
            self.vpn_server_id = cloud_info["vpn"]["server_id"]
        if "cascaded" in cloud_info.keys():
            self.cascaded_server_id = cloud_info["cascaded"]["server_id"]
            self.tunnel_bearing_nic_id = cloud_info["cascaded"]["tunnel_bearing_nic_id"]
            self.external_api_nic_id = cloud_info["cascaded"]["external_api_nic_id"]
            self.internal_base_nic_id = cloud_info["cascaded"]["internal_base_nic_id"]
            self.port_id_bind_public_ip = cloud_info["cascaded"]["port_id_bind_public_ip"]
        if "public_ip" in cloud_info.keys():
            self.vpn_public_ip = cloud_info["public_ip"]["vpn_public_ip"]
            self.vpn_public_ip_id = cloud_info["public_ip"]["vpn_public_ip_id"]
            self.cascaded_public_ip = cloud_info["public_ip"]["cascaded_public_ip"]
            self.cascaded_public_ip_id = cloud_info["public_ip"]["cascaded_public_ip_id"]

    def _read_cloud_info(self):
        cloud_info = self.cloud_info_handler.read_cloud_info()
        return cloud_info

    def get_cloud_info(self):
        self._read_install_info()
        return self._read_cloud_info()




