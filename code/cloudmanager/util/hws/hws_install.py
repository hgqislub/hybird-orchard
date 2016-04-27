import pdb

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))

import time
import socket
from heat.openstack.common import log as logging
import cloud_util as utils
from cloudmanager.exception import *
from cloudmanager.environmentinfo import *
#import vcloud_proxy_install as proxy_installer
#import vcloud_cloudinfo as data_handler
import json
from cloudmanager.subnet_manager import SubnetManager
#from vcloudcloudpersist import VcloudCloudDataHandler
from conf_util import *
from hws_util import *
import cloudmanager.constant as constant
import pdb
LOG = logging.getLogger(__name__)

_environment_conf = os.path.join("/home/hybrid_cloud/conf/hws/",
                             'environment.conf')
_install_conf = os.path.join("/home/hybrid_cloud/conf/hws/",
                             'hws_access_cloud_install.conf')
_vpc_conf = os.path.join("/home/hybrid_cloud/conf/hws/",
                             'hws_vpc.conf')
SUBNET_GATEWAY_TAIL_IP = "1"
VPN_TAIL_IP = "254"
ROOT_VOLUME_TYPE = 'SATA'

class HwsCascadedInstaller(utils.CloudUtil):
    def __init__(self, cloud_params):
        self._init_params(cloud_params)
        self._read_env()
        self._read_vpc_conf()
        self._read_install_conf()


    def _init_params(self, cloud_params):
        self.cloud_info = cloud_params
        self.cloud_id = "@".join([cloud_params['project_id'], cloud_params['azname']])
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

    def _read_vcloud_access_cloud(self):
        cloud_info = data_handler.get_vcloud_access_cloud(self.cloud_id)
        if not cloud_info:
            return

        if "vdc_network" in cloud_info.keys():
            vdc_network_info = cloud_info["vdc_network"]

            self.api_gw=vdc_network_info["api_gw"],
            self.api_subnet_cidr=vdc_network_info["api_subnet_cidr"]
            self.tunnel_gw=vdc_network_info["tunnel_gw"]
            self.tunnel_subnet_cidr=vdc_network_info["tunnel_subnet_cidr"]


        if "cascaded" in cloud_info.keys():
            cascaded_info = cloud_info["cascaded"]
            self.public_ip_api_reverse = cascaded_info["public_ip_api_reverse"]
            self.public_ip_api_forward = cascaded_info["public_ip_api_forward"]
            self.public_ip_ntp_server = cascaded_info["public_ip_ntp_server"]
            self.public_ip_ntp_client = cascaded_info["public_ip_ntp_client"]
            self.public_ip_cps_web = cascaded_info["public_ip_cps_web"]

            self.cascaded_base_ip= cascaded_info["cascaded_base_ip"]
            self.cascaded_api_ip= cascaded_info["cascaded_api_ip"]
            self.cascaded_tunnel_ip= cascaded_info["cascaded_tunnel_ip"]

        if "vpn" in cloud_info.keys():
            vpn_info = cloud_info["vpn"]
            self.public_ip_vpn = vpn_info["public_ip_vpn"]
            self.vpn_api_ip =  vpn_info["vpn_api_ip"]
            self.vpn_tunnel_ip =  vpn_info["vpn_tunnel_ip"]


        if "ext_net_eips" in cloud_info.keys():
            self.ext_net_eips = cloud_info["ext_net_eips"]

    def _create_vpc(self):
        name = self.vpc_info["name"]
        cidr = self.vpc_info["cidr"]
        self.vpc_id = self.installer.create_vpc(name, cidr)

    def _delete_vpc(self):
        self.installer.delete_vpc(self.vpc_id)

    def _create_subnet(self):
        az = self.cloud_info["availability_zone"]
        self.external_api_cidr = self.external_api_info["cidr"]
        external_api_gateway = self._get_gateway_ip(self.external_api_cidr)
        self.tunnel_bearing_cidr = self.tunnel_bearing_info["cidr"]
        tunnel_bearing_gateway = self._get_gateway_ip(self.tunnel_bearing_cidr)
        self.internal_base_cidr = self.internal_base_info["cidr"]
        internal_base_gateway = self._get_gateway_ip(self.internal_base_cidr)
        self.debug_cidr = self.debug_info["cidr"]
        debug_gateway = self._get_gateway_ip(self.debug_cidr)

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

    def _delete_subnet(self):
        self.installer.delete_subnet(self.external_api_id)
        self.installer.delete_subnet(self.tunnel_bearing_id)
        self.installer.delete_subnet(self.internal_base_id)
        self.installer.delete_subnet(self.debug_id)

    @staticmethod
    def _get_gateway_ip(cidr):
        ip_list = cidr.split(".")
        gateway_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], SUBNET_GATEWAY_TAIL_IP])
        return gateway_ip

    @staticmethod
    def _get_vpn_ip(cidr):
        ip_list = cidr.split(".")
        vpn_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], VPN_TAIL_IP])
        return vpn_ip

    def _get_free_public_ip(self):
        result = self.installer.get_free_public_ip()
        self.vpn_public_ip = result["public_ip_address"]
        self.vpn_public_ip_id = result["id"]

    def _release_public_ip(self):
        self.installer.release_public_ip()

    def cloud_preinstall(self):
        pdb.set_trace()
        self.install_network()
        self.install_vpn()

    def install_network(self):
        self._create_vpc()
        self._create_subnet()

    def uninstall_network(self):
        self._delete_subnet()
        self._delete_vpc()

    def cloud_postinstall(self, cloudinfo):
        VcloudCloudDataHandler().add_vcloud_cloud(cloudinfo)

    def cloud_postuninstall(self):
        #delete vdc network
        self.installer_login()
        network_num = self.installer.get_networks(vdc_name=self.vcloud_vdc)
        #pdb.set_trace()
        while(len(network_num) > 0 ):
            self.uninstall_network()
            network_num = self.installer.get_networks(vdc_name=self.vcloud_vdc)
        self.installer_logout()

    def install_cascaded(self):
         #pdb.set_trace()
         self._install_cascaded()

    def _install_cascaded(self):
        nics = [{"subnet_id": self.external_api_id},
                {"subnet_id": self.tunnel_bearing_id},
                {"subnet_id": self.internal_base_id},
                {"subnet_id": self.debug_id}]
        job_id = self.installer.create_vm(self.cascaded_image,
                                  self.cascaded_flavor,
                                  "cascaded_vm", self.vpc_id,
                                  nics,ROOT_VOLUME_TYPE,
                                  self.availability_zone,
                                  adminPass=constant.Cascaded.ROOT_PWD)
        self.cascaded_server_id = self.installer.block_until_success(job_id)

        data_handler.write_cascaded(self.cloud_id,
                                    self.public_ip_api_reverse,
                                    self.public_ip_api_forward,
                                    self.public_ip_ntp_server,
                                    self.public_ip_ntp_client,
                                    self.public_ip_cps_web,
                                    self.cascaded_base_ip,
                                    self.cascaded_api_ip,
                                    self.cascaded_tunnel_ip)

        LOG.info("install cascaded success.")

    def uninstall_cascaded(self):
        self._uninstall_cascaded()

    def _uninstall_cascaded(self):
        servers = [self.cascaded_server_id]
        self.installer.delete_vm(servers, True, True)

    def install_vpn(self):
        self._install_vpn()

    def _install_vpn(self):
        self._get_free_public_ip()
        publicip = dict()
        publicip["id"]= self.vpn_public_ip_id
        self.vpn_external_api_ip = self._get_vpn_ip(self.external_api_cidr)
        self.vpn_tunnel_bearing_id = self._get_vpn_ip(self.tunnel_bearing_cidr)

        nics = [{"subnet_id": self.external_api_id,
                             "ip_address": self.vpn_external_api_ip},
                            {"subnet_id": self.tunnel_bearing_id,
                             "ip_address": self.vpn_tunnel_bearing_id}]
        job_id = self.installer.create_vm( self.vpn_image,
                                  self.vpn_flavor, "cascaded_vpn",
                                  self.vpc_id, nics,
                                  ROOT_VOLUME_TYPE,
                                  self.availability_zone,
                                  public_ip_id=self.vpn_public_ip_id,
                                  adminPass=constant.VpnConstant.VPN_ROOT_PWD)
        job_id = "8aace0c8540b15c301545746e8b17f7e"
        self.vpn_server_id = self.installer.block_until_success(job_id)

    def uninstall_vpn(self):
        self._uninstall_vpn()

    def _uninstall_vpn(self):
        servers = [self.vpn_server_id]
        self.installer.delete_vm(servers, True, True)

    def package_installinfo(self):
        return self.package_vcloud_access_cloud_info()

    def package_vcloud_access_cloud_info(self):
        #TODO(lrx):modify the info params
        info = {"vdc_network":
                    {"api_gw": self.api_gw,
                    "api_subnet_cidr": self.api_subnet_cidr,
                    "tunnel_gw": self.tunnel_gw,
                    "tunnel_subnet_cidr": self.tunnel_subnet_cidr
                     },
                "cascaded":
                    {"public_ip_api_reverse": self.public_ip_api_reverse,
                     "public_ip_api_forward": self.public_ip_api_forward,
                     "public_ip_ntp_server": self.public_ip_ntp_server,
                     "public_ip_ntp_client": self.public_ip_ntp_client,
                     "public_ip_cps_web": self.public_ip_cps_web,
                     "base_ip": self.cascaded_base_ip,
                     "api_ip": self.cascaded_api_ip,
                     "tunnel_ip": self.cascaded_tunnel_ip},
                "vpn":
                    {
                     "public_ip_vpn":self.public_ip_vpn,
                     "vpn_api_ip":self.vpn_api_ip,
                     "vpn_tunnel_ip":self.vpn_tunnel_ip},

                "ext_net_eips": self.ext_net_eips.keys()}
        return info

    def get_vcloud_access_cloud_install_info(self,installer):
                return installer.package_vcloud_access_cloud_info()






