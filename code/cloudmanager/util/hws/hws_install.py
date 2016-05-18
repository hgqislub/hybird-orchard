
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))

import time
import socket
from heat.openstack.common import log as logging
import cloud_util as utils
from cloudmanager.exception import *
from cloudmanager.environmentinfo import *
import json
from cloudmanager.subnet_manager import SubnetManager
from hws_util import *
from hws_cloud_info_persist import *
import cloudmanager.constant as constant
from hws_cloudinfo import HwsCloudInfo
import pdb

LOG = logging.getLogger(__name__)

_environment_conf = os.path.join("/home/hybrid_cloud/conf/hws/",
                             'environment.conf')
_install_conf = os.path.join("/home/hybrid_cloud/conf/hws/",
                             'hws_access_cloud_install.conf')
_vpc_conf = os.path.join("/home/hybrid_cloud/conf/hws/",
                             'hws_vpc.conf')
_access_cloud_install_info_file = os.path.join("/home/hybrid_cloud/data/hws/",
                             'hws_access_cloud_install.data')
_access_cloud_info_file = os.path.join("/home/hybrid_cloud/data/hws/",
                             'hws_access_cloud.data')

SUBNET_GATEWAY_TAIL_IP = "1"
VPN_TAIL_IP = "254"
CASCADED_TAIL_IP = "4"
ROOT_VOLUME_TYPE = 'SATA'

class HwsCascadedInstaller(utils.CloudUtil):
    def __init__(self, cloud_params):
        self._init_params(cloud_params)
        self._read_env()
        #start_hws_gateway(self.cascading_api_ip, constant.Cascading.ROOT,
        #                   constant.Cascading.ROOT_PWD)
        self._read_vpc_conf()
        self._read_install_conf()
        self._read_access_cloud_install_info()

    def _init_params(self, cloud_params):
        self.cloud_info = cloud_params
        self.cloud_id = "@".join(["HWS", cloud_params['project_id'], cloud_params['azname']])
        self.installer = HwsInstaller(cloud_params)
        self.availability_zone = cloud_params["availability_zone"]
        self.install_data_handler = HwsCloudInfoPersist(_access_cloud_install_info_file, self.cloud_id)
        self.cloud_info_handler = HwsCloudInfoPersist(_access_cloud_info_file, self.cloud_id)

    def _read_env(self):
        try:
            env_info = read_conf(_environment_conf)
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
        except IOError as e:
            error = "read file = %s error" % _environment_conf
            LOG.error(e)
            raise ReadEnvironmentInfoFailure(error = error)
        except KeyError as e:
            error = "read key = %s error in file = %s" % (e.message, _environment_conf)
            LOG.error(error)
            raise ReadEnvironmentInfoFailure(error = error)

    def _read_install_conf(self):
        try:
            install_info = read_conf(_install_conf)
            self.cascaded_image = install_info["cascaded_image"]
            self.cascaded_flavor = install_info["cascaded_flavor"]
            self.vpn_image = install_info["vpn_image"]
            self.vpn_flavor = install_info["vpn_flavor"]

        except IOError as e:
            error = "read file = %s error" % _install_conf
            LOG.error(e)
            raise ReadEnvironmentInfoFailure(error = error)
        except KeyError as e:
            error = "read key = %s error in file = %s" % (e.message, _install_conf)
            LOG.error(error)
            raise ReadEnvironmentInfoFailure(error = error)

    def _read_vpc_conf(self):
        try:
            vpc_conf = read_conf(_vpc_conf)
            self.vpc_info = vpc_conf["vpc_info"]
            self.external_api_info = vpc_conf["external_api_info"]
            self.tunnel_bearing_info = vpc_conf["tunnel_bearing_info"]
            self.internal_base_info = vpc_conf["internal_base_info"]
            self.debug_info = vpc_conf["debug_info"]

        except IOError as e:
            error = "read file = %s error" % _vpc_conf
            LOG.error(e)
            raise ReadEnvironmentInfoFailure(error = error)
        except KeyError as e:
            error = "read key = %s error in file = %s" % (e.message, _vpc_conf)
            LOG.error(error)
            raise ReadEnvironmentInfoFailure(error = error)

    def _create_vpc(self):
        name = self.vpc_info["name"]
        cidr = self.vpc_info["cidr"]
        if self.vpc_id is None:
            self.vpc_id = self.installer.create_vpc(name, cidr)

        self.security_group_id = self.installer.get_security_group(self.vpc_id)

        #self.installer.create_security_group_rule(
        #        self.security_group_id, "ingress", "IPv4")

        self.install_data_handler.write_vpc_info(self.vpc_id, name, cidr)

    def _delete_vpc(self):
        self.installer.delete_vpc(self.vpc_id)

    def _create_subnet(self):
        az = self.cloud_info["availability_zone"]
        self.external_api_cidr = self.external_api_info["cidr"]
        self.external_api_gateway = self._alloc_gateway_ip(self.external_api_cidr)
        self.tunnel_bearing_cidr = self.tunnel_bearing_info["cidr"]
        tunnel_bearing_gateway = self._alloc_gateway_ip(self.tunnel_bearing_cidr)
        self.internal_base_cidr = self.internal_base_info["cidr"]
        internal_base_gateway = self._alloc_gateway_ip(self.internal_base_cidr)
        self.debug_cidr = self.debug_info["cidr"]
        debug_gateway = self._alloc_gateway_ip(self.debug_cidr)

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
        self.install_data_handler.write_subnets_info(external_api_info, tunnel_bearing_info, internal_base_info, debug_info)

    def _delete_subnet(self):
        self.installer.delete_subnet(self.external_api_id)
        self.installer.delete_subnet(self.tunnel_bearing_id)
        self.installer.delete_subnet(self.internal_base_id)
        self.installer.delete_subnet(self.debug_id)

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
        pdb.set_trace()
        if self.vpn_public_ip_id is None:
            result = self.installer.alloc_public_ip()
            self.vpn_public_ip = result["public_ip_address"]
            self.vpn_public_ip_id = result["id"]

        self.install_data_handler.write_public_ip_info(
                self.vpn_public_ip,
                self.vpn_public_ip_id
                )

    def _alloc_cascaded_public_ip(self):
        pdb.set_trace()
        if self.cascaded_public_ip_id is None:
            result = self.installer.alloc_public_ip()
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
        self._install_network()

    def _install_network(self):
        self._create_vpc()
        self._create_subnet()

    def _uninstall_network(self):
        self._delete_subnet()
        self._delete_vpc()

    def cloud_postinstall(self, cloudinfo):
        pass

    def cloud_postuninstall(self):
        self.install_data_handler.delete_cloud_info()
        self.cloud_info_handler.delete_cloud_info()

    def cloud_install(self):
        self._cloud_install()

    def _cloud_install(self):
        self._install_vpn()
        self._install_cascaded()

    def cloud_uninstall(self):
        #self._cloud_uninstall()
        pass

    def _cloud_uninstall(self):
        self.uninstall_cascaded()
        self.uninstall_vpn()
        self.installer.block_until_delete_resource_success(self.delete_cascaded_job_id)
        self.installer.block_until_delete_resource_success(self.delete_vpn_job_id)
        self._uninstall_network()

    def _install_cascaded(self):
        pdb.set_trace()
        self.cascaded_internal_base_ip = self._alloc_cascaded_ip(self.internal_base_cidr, "12")
        self.cascaded_tunnel_bearing_ip = self._alloc_cascaded_ip(self.tunnel_bearing_cidr, "4")
        self.cascaded_external_api_ip = self._alloc_cascaded_ip(self.external_api_cidr, "4")
        self.cascaded_debug_ip = self._alloc_cascaded_ip(self.debug_cidr, "4")

        nics = [{"subnet_id": self.debug_id,
                 "ip_address": self.cascaded_debug_ip}]
        security_groups = [self.security_group_id]
        if self.cascaded_server_id is None:
            self.cascaded_server_job_id = self.installer.create_vm(self.cascaded_image,
                                  self.cascaded_flavor,
                                  "hgq_cascaded", self.vpc_id,
                                  nics,ROOT_VOLUME_TYPE,
                                  self.availability_zone,
                                  adminPass = constant.Cascaded.ROOT_PWD,
                                  security_groups = security_groups)
            self.cascaded_server_id = self.installer.block_until_create_vm_success(self.cascaded_server_job_id)
            self._create_cascaded_nics()
        self.install_data_handler.write_cascaded_info(self.cascaded_server_id,
                                                      self.cascaded_public_ip,
                                                      self.cascaded_external_api_ip,
                                                      self.cascaded_tunnel_bearing_ip)

        if self.vpn_server_id is None:
            self.vpn_server_id = self.installer.block_until_create_vm_success(self.vpn_server_job_id)

        self.install_data_handler.write_vpn(self.vpn_server_id, self.vpn_public_ip,
                                            self.vpn_external_api_ip, self.vpn_tunnel_bearing_ip)
        LOG.info("install cascaded success.")

    def _create_cascaded_nics(self):
        ##nic should add one by one to maintain right sequence
        pdb.set_trace()
        security_groups = [{"id":self.security_group_id}]
        """
        job_id = self.installer.add_nics(self.cascaded_server_id, self.internal_base_id,
                                security_groups, self.cascaded_internal_base_ip)
        self.installer.block_until_create_nic_success(job_id)
        job_id = self.installer.add_nics(self.cascaded_server_id, self.external_api_id,
                                security_groups, self.cascaded_external_api_ip)
        external_api_nic_id = self.installer.block_until_create_nic_success(job_id)
"""
        external_api_nic_id = "b2bf279d-139d-4479-bdf3-5e2e9c860bdb"
        external_port_id = self.installer.get_external_api_port_id(
                self.cascaded_server_id, external_api_nic_id)
        self._alloc_cascaded_public_ip()
        self.installer.bind_public_ip(self.cascaded_public_ip_id, external_port_id)
        """
        job_id = self.installer.add_nics(self.cascaded_server_id, self.tunnel_bearing_id,
                                security_groups, self.cascaded_tunnel_bearing_ip)
        self.installer.block_until_create_nic_success(job_id)

        self.installer.reboot(self.cascaded_server_id, "SOFT")
"""
    def uninstall_cascaded(self):
        self._uninstall_cascaded()

    def _uninstall_cascaded(self):
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
        if self.vpn_server_id is None:
            self.vpn_server_job_id = self.installer.create_vm(
                self.vpn_image,
                self.vpn_flavor, "hgq_hws_cascaded_vpn",
                self.vpc_id, nics,
                ROOT_VOLUME_TYPE,
                self.availability_zone,
                public_ip_id=self.vpn_public_ip_id,
                adminPass=constant.VpnConstant.VPN_ROOT_PWD,
                security_groups=[self.security_group_id])

    def uninstall_vpn(self):
        self._uninstall_vpn()

    def _uninstall_vpn(self):
        servers = [self.vpn_server_id]
        self.delete_vpn_job_id = self.installer.delete_vm(servers, True, True)

    def package_installinfo(self):
        return self.package_hws_access_cloud_info()

    def _distribute_cloud_domain(self, region_name, azname, az_tag):
        domain_list = self.cascading_domain.split(".")
        domainpostfix = ".".join([domain_list[2], domain_list[3]])
        l_region_name = region_name.lower()
        cloud_cascaded_domain = ".".join(
                [azname, l_region_name + az_tag, domainpostfix])
        self.cascaded_aggregate = ".".join([azname, l_region_name + az_tag])
        return cloud_cascaded_domain

    def package_hws_access_cloud_info(self):
        cascaded_vpn_info = {
            "public_ip": self.vpn_public_ip,
            "external_api_ip": self.vpn_external_api_ip,
            "tunnel_bearing_ip": self.vpn_tunnel_bearing_ip
        }

        cascaded_info = {
            "public_ip": self.cascaded_public_ip,
            "external_api_ip": self.cascaded_external_api_ip,
            "tunnel_bearing_ip": self.cascaded_tunnel_bearing_ip,
            "domain": self._distribute_cloud_domain(
                     self.cloud_info['region'], self.cloud_info['azname'], "--hws"),
            "aggregate": self.cascaded_aggregate
        }

        cascaded_subnets_info = {
            "vpc_id": self.vpc_id,
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
            "public_ip": self.local_vpn_public_gw,
            "external_api_ip": self.local_vpn_api_ip,
            "tunnel_bearing_ip": self.local_vpn_tunnel_ip
        }

        cascading_subnets_info = {
            "external_api": self.local_api_subnet,
            "tunnel_bearing": self.local_tunnel_subnet
        }

        vpn_conn_name = {
            "api_conn_name": self.cloud_id + '-api',
            "tunnel_conn_name": self.cloud_id + '-tunnel'
        }

        info = {"cascaded_vpn_info":cascaded_vpn_info,
                "cascading_vpn_info":cascading_vpn_info,
                "cascaded_info": cascaded_info,
                "cascading_info":cascading_info,
                "cascaded_subnets_info": cascaded_subnets_info,
                "cascading_subnets_info": cascading_subnets_info,
                "vpn_conn_name": vpn_conn_name
                }
        self.cloud_info_handler.write_cloud_info(info)
        return info

    def _read_access_cloud_install_info(self):
        self.vpc_id = None
        self.internal_base_id = None
        self.debug_id = None
        self.external_api_id = None
        self.tunnel_bearing_id = None
        self.vpn_server_id = None
        self.cascaded_server_id = None
        self.cascaded_public_ip_id = None
        self.vpn_public_ip_id = None
        cloud_info = self.install_data_handler.read_cloud_info()
        if "vpc" in cloud_info.keys():
            self.vpc_id = cloud_info["vpc"]["id"]
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
        if "public_ip" in cloud_info.keys():
            self.vpn_public_ip = cloud_info["public_ip"]["vpn_public_ip"]
            self.vpn_public_ip_id = cloud_info["public_ip"]["vpn_public_ip_id"]
            self.cascaded_public_ip = cloud_info["public_ip"]["cascaded_public_ip"]
            self.cascaded_public_ip_id = cloud_info["public_ip"]["cascaded_public_ip_id"]

    def _read_access_cloud_info(self):
        cloud_info = self.cloud_info_handler.read_cloud_info()
        return cloud_info

    def get_vcloud_access_cloud_install_info(self, installer):
        self._read_access_cloud_install_info()
        return self._read_access_cloud_info()

    def get_vcloud_cloud(self):
        return HwsCloudInfo()




