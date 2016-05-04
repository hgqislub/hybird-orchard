
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
from conf_util import *
from hws_util import *
from hws_cloud_info_persist import *
import cloudmanager.constant as constant
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
CASCADED_TAIL_IP = "253"
ROOT_VOLUME_TYPE = 'SATA'

class HwsCascadedInstaller(utils.CloudUtil):
    def __init__(self, cloud_params):
        self._init_params(cloud_params)
        self._read_env()
        self._read_vpc_conf()
        self._read_install_conf()
        self.data_handler = HwsCloudInfoPersist(_access_cloud_install_info_file, self.cloud_id)


    def _init_params(self, cloud_params):
        self.cloud_info = cloud_params
        self.cloud_id = "@".join(["HWS", cloud_params['project_id'], cloud_params['azname']])
        self.installer = HwsInstaller(cloud_params)
        self.availability_zone = cloud_params["availability_zone"]

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
        self.vpc_id = self.installer.create_vpc(name, cidr)
        self.data_handler.write_vpc_info(self.vpc_id, name, cidr)

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

        self.external_api_id = self.installer.create_subnet("external_api",
                                self.external_api_cidr, az, external_api_gateway,
                                self.vpc_id)
        self.tunnel_bearing_id = self.installer.create_subnet("tunnel_bearing",
                              self.tunnel_bearing_cidr, az, tunnel_bearing_gateway,
                              self.vpc_id)
        self.internal_base_id = self.installer.create_subnet("internal_base",
                              self.internal_base_cidr, az, internal_base_gateway,
                              self.vpc_id)
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
        self.data_handler.write_subnets_info(external_api_info, tunnel_bearing_info, internal_base_info, debug_info)

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
    def _alloc_cascaded_ip(cidr):
        ip_list = cidr.split(".")
        cascaded_ip = ".".join([ip_list[0], ip_list[1], ip_list[2], CASCADED_TAIL_IP])
        return cascaded_ip
    
    def _alloc_public_ip(self):
        result = self.installer.alloc_public_ip()
        self.vpn_public_ip = result["public_ip_address"]
        self.vpn_public_ip_id = result["id"]

    def _release_public_ip(self):
        self.installer.release_public_ip()

    def cloud_preinstall(self):
        pdb.set_trace()
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
        pass

    def cloud_install(self):
        self._cloud_install()

    def _cloud_install(self):
        self._install_vpn()
        self._install_cascaded()

    def _install_cascaded(self):
        self.cascaded_internal_base_ip = self._alloc_cascaded_ip(self.internal_base_cidr)
        self.cascaded_tunnel_bearing_ip = self._alloc_cascaded_ip(self.tunnel_bearing_cidr)
        self.cascaded_external_api_ip = self._alloc_cascaded_ip(self.external_api_cidr)
        self.cascaded_debug_ip = self._alloc_cascaded_ip(self.internal_debug_cidr)

        nics = [{"subnet_id": self.external_api_id,
                 "ip_address": self.cascaded_external_api_ip},
                {"subnet_id": self.tunnel_bearing_id,
                 "ip_address": self.cascaded_tunnel_bearing_ip},
                {"subnet_id": self.internal_base_id,
                 "ip_address": self.cascaded_internal_base_ip},
                {"subnet_id": self.debug_id,
                 "ip_address": self.cascaded_debug_ip}]
        self.cascaded_server_job_id = self.installer.create_vm(self.cascaded_image,
                                  self.cascaded_flavor,
                                  "hgq_hws_cascaded", self.vpc_id,
                                  nics,ROOT_VOLUME_TYPE,
                                  self.availability_zone,
                                  adminPass=constant.Cascaded.ROOT_PWD)
        self.cascaded_server_id = self.installer.block_until_success(self.cascaded_server_job_id)
        self.data_handler.write_cascaded_info(self.cascaded_server_id)
        LOG.info("install cascaded success.")

    def uninstall_cascaded(self):
        self._uninstall_cascaded()

    def _uninstall_cascaded(self):
        servers = [self.cascaded_server_id]
        self.installer.delete_vm(servers, True, True)

    def _install_vpn(self):
        self._alloc_public_ip()
        publicip = dict()
        publicip["id"]= self.vpn_public_ip_id
        self.vpn_external_api_ip = self._alloc_vpn_ip(self.external_api_cidr)
        self.vpn_tunnel_bearing_ip = self._alloc_vpn_ip(self.tunnel_bearing_cidr)

        nics = [{"subnet_id": self.external_api_id,
                             "ip_address": self.vpn_external_api_ip},
                            {"subnet_id": self.tunnel_bearing_id,
                             "ip_address": self.vpn_tunnel_bearing_ip}]
        self.vpn_server_job_id = self.installer.create_vm( self.vpn_image,
                                  self.vpn_flavor, "hgq_hws_cascaded_vpn",
                                  self.vpc_id, nics,
                                  ROOT_VOLUME_TYPE,
                                  self.availability_zone,
                                  public_ip_id=self.vpn_public_ip_id,
                                  adminPass=constant.VpnConstant.VPN_ROOT_PWD)
        self.vpn_server_id = self.installer.block_until_success(self.vpn_server_job_id)

        self.data_handler.write_vpn(self.vpn_server_id, self.vpn_public_ip,
                                    self.vpn_external_api_ip, self.vpn_tunnel_bearing_ip)

    def uninstall_vpn(self):
        self._uninstall_vpn()

    def _uninstall_vpn(self):
        servers = [self.vpn_server_id]
        self.installer.delete_vm(servers, True, True)

    def package_installinfo(self):
        return self.package_vcloud_access_cloud_info()

    def _distribute_cloud_domain(self, region_name, azname, az_tag):
        domain_list = self.cascading_domain.split(".")
        domainpostfix = ".".join([domain_list[2], domain_list[3]])
        l_region_name = region_name.lower()
        cloud_cascaded_domain = ".".join(
                [azname, l_region_name + az_tag, domainpostfix])
        return cloud_cascaded_domain

    def package_hws_access_cloud_info(self):
        cascaded_vpn_info = {
            "public_ip": self.vpn_public_ip,
            "external_api_ip": self.vpn_external_api_ip,
            "tunnel_bearing_ip": self.vpn_tunnel_bearing_ip
        }

        cascaded_info = {
            "external_api_ip": self.cascaded_external_api_ip,
            "tunnel_bearing_ip": self.cascaded_tunnel_bearing_ip,
            "domain": self._distribute_cloud_domain(
                    self.cloud_info['azname'], self.cloud_info['region'], "hws")
        }

        cascaded_subnets_info = {
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
        data_handler = HwsCloudInfoPersist(_access_cloud_info_file, self.cloud_id)
        data_handler.write_cloud_info(info)
        return info

    def get_vcloud_access_cloud_install_info(self):
        return self.package_vcloud_access_cloud_info()






