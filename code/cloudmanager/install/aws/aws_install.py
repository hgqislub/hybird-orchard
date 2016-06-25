
from heat.openstack.common import log as logging

import heat.engine.resources.cloudmanager.util.conf_util as conf_util
from heat.engine.resources.cloudmanager.util.subnet_manager import SubnetManager
from heat.engine.resources.cloudmanager.util.cloud_manager_exception import *
import heat.engine.resources.cloudmanager.util.proxy_manager as proxy_manager
import heat.engine.resources.cloudmanager.util.constant as constant
from region_mapping import *
import aws_util
import aws_access_cloud_data_handler as data_handler
from aws_cloud_info_persist import *

import pdb

LOG = logging.getLogger(__name__)

SUBNET_GATEWAY_TAIL_IP = "1"
VPN_TAIL_IP = "254"
CASCADED_TAIL_IP = "4"
ROOT_VOLUME_TYPE = 'SATA'

class AwsCascadedInstaller(object):
    def __init__(self, cloud_params):
        self._init_params(cloud_params)
        self._read_env()
        self._read_install_info()

    def _init_params(self, cloud_params):
        self.cloud_params = cloud_params
        self.cloud_id = "@".join(["AWS", self.cloud_params['azname']])
        self.region = get_region_id(cloud_params["region"])
        self.az = cloud_params["availabilityzone"]
        access_key = cloud_params["access_key"]
        secret_key = cloud_params["secret_key"]

        self.installer = aws_util.AWSInstaller(access_key, secret_key, self.region, self.az)

        self._read_default_conf()
        self.cascaded_image = self.default_cascaded_image
        self.cascaded_vm_type = self.default_cascaded_flavor
        self.vpn_image = self.default_vpn_image
        self.vpn_vm_type = self.default_vpn_flavor

        self.install_data_handler = \
            AwsCloudInfoPersist(constant.AwsConstant.INSTALL_INFO_FILE, self.cloud_id)
        self.cloud_info_handler = \
            AwsCloudInfoPersist(constant.AwsConstant.CLOUD_INFO_FILE, self.cloud_id)

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

            if self.cascading_vpn_public_gw == self.cascading_eip:
                self.green_ips = [self.cascading_vpn_public_gw]
            else:
                self.green_ips = [self.cascading_vpn_public_gw, self.cascading_eip]

        except IOError as e:
            error = "read file = %s error" % constant.Cascading.ENV_FILE
            LOG.error(e)
            raise ReadEnvironmentInfoFailure(error = error)
        except KeyError as e:
            error = "read key = %s error in file = %s" % (e.message, constant.Cascading.ENV_FILE)
            LOG.error(error)
            raise ReadEnvironmentInfoFailure(error = error)

    def _read_default_conf(self):
        try:
            self.default_params = conf_util.read_conf(constant.AwsConstant.CONF_FILE)
            image_info = self.default_params["image"]
            self.default_cascaded_image = image_info["cascaded_image"]
            self.default_cascaded_flavor = image_info["cascaded_flavor"]
            self.default_vpn_image = image_info["vpn_image"]
            self.default_vpn_flavor = image_info["vpn_flavor"]

            network = self.default_params["network"]
            self.default_vpc_cidr = network["vpc_cidr"]
            self.default_external_api_cidr = network["external_api_cidr"]
            self.default_tunnel_bearing_cidr = network["tunnel_bearing_cidr"]
            self.default_internal_base_cidr = network["internal_base_cidr"]
            self.default_debug_cidr = network["debug_cidr"]

        except IOError as e:
            error = "read file = %s error" % constant.AwsConstant.CONF_FILE
            LOG.error(e)
            raise ReadEnvironmentInfoFailure(error = error)
        except KeyError as e:
            error = "read key = %s error in file = %s" % (e.message, constant.AwsConstant.CONF_FILE)
            LOG.error(error)
            raise ReadEnvironmentInfoFailure(error = error)

    def _read_install_info(self):
        self.vpc_id = None
        self.debug_subnet_cidr = None
        self.debug_subnet_id = None
        self.base_subnet_cidr = None
        self.base_subnet_id = None
        self.api_subnet_cidr = None
        self.api_subnet_id = None
        self.tunnel_subnet_cidr = None
        self.tunnel_subnet_id = None
        self.gateway_id = None
        self.rtb_id = None

        self.cascaded_vm = None
        self.cascaded_vm_id = None
        self.cascaded_debug_ip = None
        self.cascaded_debug_interface_id = None
        self.cascaded_base_ip = None
        self.cascaded_base_interface_id = None
        self.cascaded_api_ip = None
        self.cascaded_api_interface_id = None
        self.cascaded_tunnel_ip = None
        self.cascaded_tunnel_interface_id = None
        self.cascaded_eip_public_ip = None
        self.cascaded_eip_allocation_id = None

        self.vpn_vm = None
        self.vpn_vm_id = None
        self.vpn_api_ip = None
        self.vpn_tunnel_ip = None
        self.vpn_eip_public_ip = None
        self.vpn_eip_allocation_id = None
        self.vpn_api_interface_id = None
        self.vpn_tunnel_interface_id = None
        self.proxy_info = None

        self.ext_net_eips = {}

        cloud_info = self.install_data_handler.read_cloud_info()
        if cloud_info is None:
            return
        if "proxy_info" in cloud_info.keys():
            self.proxy_info = cloud_info["proxy_info"]

        if "subnets_cidr" in cloud_info.keys():
            subnet_cidr = cloud_info["subnets_cidr"]
            self.vpc_cidr = subnet_cidr["vpc_cidr"]
            self.external_api_cidr = subnet_cidr["external_api_cidr"]
            self.tunnel_bearing_cidr = subnet_cidr["tunnel_bearing_cidr"]
            self.internal_base_cidr = subnet_cidr["internal_base_cidr"]
            self.debug_cidr = subnet_cidr["debug_cidr"]

        if "vpc" in cloud_info.keys():
            vpc_info = cloud_info["vpc"]
            self.vpc_id = vpc_info["vpc_id"]
            self.debug_subnet_cidr = vpc_info["debug_subnet_cidr"]
            self.debug_subnet_id = vpc_info["debug_subnet_id"]
            self.base_subnet_cidr = vpc_info["base_subnet_cidr"]
            self.base_subnet_id = vpc_info["base_subnet_id"]
            self.api_subnet_cidr = vpc_info["api_subnet_cidr"]
            self.api_subnet_id = vpc_info["api_subnet_id"]
            self.tunnel_subnet_cidr = vpc_info["tunnel_subnet_cidr"]
            self.tunnel_subnet_id = vpc_info["tunnel_subnet_id"]
            self.gateway_id = vpc_info["gateway_id"]
            self.rtb_id = vpc_info["rtb_id"]

        if "cascaded" in cloud_info.keys():
            cascaded_info = cloud_info["cascaded"]
            self.cascaded_vm_id = cascaded_info["vm_id"]
            self.cascaded_debug_ip = cascaded_info["debug_ip"]
            self.cascaded_debug_interface_id = cascaded_info["debug_interface_id"]
            self.cascaded_base_ip = cascaded_info["base_ip"]
            self.cascaded_base_interface_id = cascaded_info["base_interface_id"]
            self.cascaded_api_ip = cascaded_info["api_ip"]
            self.cascaded_api_interface_id = cascaded_info["api_interface_id"]
            self.cascaded_tunnel_ip = cascaded_info["tunnel_ip"]
            self.cascaded_tunnel_interface_id = cascaded_info["tunnel_interface_id"]
            self.cascaded_eip_public_ip = cascaded_info["eip_public_ip"]
            self.cascaded_eip_allocation_id = cascaded_info["eip_allocation_id"]

        if "vpn" in cloud_info.keys():
            vpn_info = cloud_info["vpn"]
            self.vpn_vm_id = vpn_info["vm_id"]
            self.vpn_api_ip = vpn_info["api_ip"]
            self.vpn_tunnel_ip = vpn_info["tunnel_ip"]
            self.vpn_eip_public_ip = vpn_info["eip_public_ip"]
            self.vpn_eip_allocation_id = vpn_info["eip_allocation_id"]
            self.vpn_api_interface_id = vpn_info["api_interface_id"]
            self.vpn_tunnel_interface_id = vpn_info["tunnel_interface_id"]

        if "ext_net_eips" in cloud_info.keys():
            self.ext_net_eips = cloud_info["ext_net_eips"]

    def install_network(self):
        if self.vpc_id:
            return
        # install vpc
        vpc = self.installer.create_vpc(self.vpc_cidr)
        self.vpc_id = vpc.id
        self.installer.associate_dhcp_options("default", vpc.id)

        # add internet gateway
        self.gateway_id = self.installer.create_internet_gateway()
        self.installer.attach_internet_gateway(self.gateway_id, self.vpc_id)

        # get route table id, every vpc only have one route table.
        route_tables = self.installer.get_all_route_tables(self.vpc_id)
        self.rtb_id = route_tables[0].id
        self.installer.create_route(self.rtb_id, "0.0.0.0/0",
                                    gateway_id=self.gateway_id)

        # install subnet
        self.debug_subnet_id = self.installer.create_subnet(self.vpc_id, self.debug_cidr)
        self.base_subnet_id = self.installer.create_subnet(self.vpc_id, self.internal_base_cidr)
        self.api_subnet_id = self.installer.create_subnet(self.vpc_id, self.external_api_cidr)
        self.tunnel_subnet_id = self.installer.create_subnet(self.vpc_id, self.tunnel_bearing_cidr)

        for ip in self.green_ips:
            self.add_security("%s/32" % ip)

        self.install_data_handler.write_vpc_info(self.vpc_id,
                               self.debug_cidr, self.debug_subnet_id,
                               self.internal_base_cidr, self.base_subnet_id,
                               self.external_api_cidr, self.api_subnet_id,
                               self.tunnel_bearing_cidr, self.tunnel_subnet_id,
                               self.gateway_id, self.rtb_id)

    def add_security(self, cidr):
        sgs = self.installer.get_all_security_groups(self.vpc_id)
        for sg in sgs:
            sg.authorize(ip_protocol="-1", cidr_ip=cidr)

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

    def cloud_preinstall(self):
        self._alloc_subnets_and_ips()

    def _alloc_subnets_and_ips(self):
        if self.vpc_cidr is None:
            network = self.cloud_params["network"]
            if network:
                self.vpc_cidr = network["vpc_cidr"]
                self.external_api_cidr = network["external_api_cidr"]
                self.tunnel_bearing_cidr = network["tunnel_bearing_cidr"]
                self.internal_base_cidr = network["internal_base_cidr"]
                self.debug_cidr = network["debug_cidr"]
            else:
                self.vpc_cidr = self.default_vpc_cidr
                self.debug_cidr = self.default_debug_cidr
                self.internal_base_cidr = self.default_internal_base_cidr
                subnet_manager = SubnetManager()
                subnet_pair = subnet_manager.distribute_subnet_pair\
                    (self.default_external_api_cidr,  self.default_tunnel_bearing_cidr, constant.HwsConstant.INSTALL_INFO_FILE)
                self.external_api_cidr = subnet_pair["external_api_cidr"]
                self.tunnel_bearing_cidr = subnet_pair["tunnel_bearing_cidr"]

        self.install_data_handler.write_subnets_cidr(self.vpc_cidr,
                                                     self.external_api_cidr,
                                                     self.tunnel_bearing_cidr,
                                                     self.internal_base_cidr,
                                                     self.debug_cidr )

        self.cascaded_base_ip = self._alloc_cascaded_ip(self.internal_base_cidr, "12")
        self.cascaded_tunnel_ip = self._alloc_cascaded_ip(self.tunnel_bearing_cidr, "12")
        self.cascaded_api_ip = self._alloc_cascaded_ip(self.external_api_cidr, "12")
        self.cascaded_debug_ip = self._alloc_cascaded_ip(self.debug_cidr, "12")

    def cloud_preuninstall(self):
        pass

    def cloud_postinstall(self):
        pass

    def cloud_postuninstall(self):
        #pdb.set_trace()
        self.install_data_handler.delete_cloud_info()
        self.cloud_info_handler.delete_cloud_info()

    def cloud_install(self):
        self.install_proxy()
        self.install_network()
        vpn_info = self.cloud_params["vpn_info"]
        if vpn_info and vpn_info["exist"] == "true":
            self._read_exist_vpn_info()
        else:
            self.install_vpn()
        self.install_cascaded()

    def install_proxy(self):
        if self.proxy_info is None:
            self.proxy_info = proxy_manager.distribute_proxy()
        self.install_data_handler.write_proxy(self.proxy_info)

    def install_cascaded(self):
        if self.cascaded_vm_id:
            return

        cascaded_debug_en = aws_util.AWSInterface(
                self.debug_subnet_id, self.cascaded_debug_ip)
        cascaded_base_en = aws_util.AWSInterface(
                self.base_subnet_id, self.cascaded_base_ip)
        cascaded_api_en = aws_util.AWSInterface(
                self.api_subnet_id, self.cascaded_api_ip)
        cascaded_tunnel_en = aws_util.AWSInterface(
                self.tunnel_subnet_id, self.cascaded_tunnel_ip)

        self.cascaded_vm = self.installer.create_vm(self.cascaded_image,
                                                    self.cascaded_vm_type,
                                                    cascaded_debug_en,
                                                    cascaded_base_en,
                                                    cascaded_api_en,
                                                    cascaded_tunnel_en)
        self.cascaded_vm_id = self.cascaded_vm.id

        for interface in self.cascaded_vm.interfaces:
            if self.cascaded_api_ip == interface.private_ip_address:
                self.cascaded_api_interface_id = interface.id
                continue

            if self.cascaded_base_ip == interface.private_ip_address:
                self.cascaded_base_interface_id = interface.id
                continue

            if self.cascaded_debug_ip == interface.private_ip_address:
                self.cascaded_debug_interface_id = interface.id
                continue

            if self.cascaded_tunnel_ip == interface.private_ip_address:
                self.cascaded_tunnel_interface_id = interface.id
                continue

        cascaded_eip = self.installer.allocate_elastic_address()
        self.installer.associate_elastic_address(
                eip=cascaded_eip,
                network_interface_id=self.cascaded_api_interface_id)
        self.cascaded_eip_public_ip = cascaded_eip.public_ip
        self.cascaded_eip_allocation_id = cascaded_eip.allocation_id

        self.install_data_handler.write_cascaded_info(self.cascaded_vm_id,
                                    self.cascaded_eip_public_ip,
                                    self.cascaded_eip_allocation_id,
                                    self.cascaded_debug_ip,
                                    self.cascaded_debug_interface_id,
                                    self.cascaded_base_ip,
                                    self.cascaded_base_interface_id,
                                    self.cascaded_api_ip,
                                    self.cascaded_api_interface_id,
                                    self.cascaded_tunnel_ip,
                                    self.cascaded_tunnel_interface_id)

    def install_vpn(self):
        if self.vpn_vm_id:
            return

        # install vpn vm
        self.vpn_api_ip = self._alloc_vpn_ip(self.external_api_cidr)
        self.vpn_tunnel_ip = self._alloc_vpn_ip(self.tunnel_bearing_cidr)

        vpn_api_en = aws_util.AWSInterface(
                self.api_subnet_id, self.vpn_api_ip)
        vpn_tunnel_en = aws_util.AWSInterface(
                self.tunnel_subnet_id, self.vpn_tunnel_ip)

        self.vpn_vm = self.installer.create_vm(self.vpn_image,
                                               self.vpn_vm_type,
                                               vpn_api_en, vpn_tunnel_en)
        self.vpn_vm_id = self.vpn_vm.id

        for interface in self.vpn_vm.interfaces:
            if self.vpn_api_ip == interface.private_ip_address:
                self.vpn_api_interface_id = interface.id

            elif self.vpn_tunnel_ip == interface.private_ip_address:
                self.vpn_tunnel_interface_id = interface.id

        self.installer.disable_network_interface_sdcheck(
                self.vpn_api_interface_id)
        self.installer.disable_network_interface_sdcheck(
                self.vpn_tunnel_interface_id)

        vpn_eip = self.installer.allocate_elastic_address()
        self.installer.associate_elastic_address(
                eip=vpn_eip, network_interface_id=self.vpn_api_interface_id)
        self.vpn_eip_public_ip = vpn_eip.public_ip
        self.vpn_eip_allocation_id = vpn_eip.allocation_id

        self.add_route("api", self.cascading_api_subnet)
        self.add_route("tunnel", self.cascading_tunnel_subnet)

        self.install_data_handler.write_vpn_info(
                               self.vpn_vm_id,
                               self.vpn_eip_public_ip,
                               self.vpn_eip_allocation_id,
                               self.vpn_api_ip, self.vpn_tunnel_ip,
                               self.vpn_api_interface_id,
                               self.vpn_tunnel_interface_id)

    def _read_exist_vpn_info(self):
        vpn_info = self.cloud_params["vpn_info"]
        self.vpn_public_ip = vpn_info["public_ip"],
        self.vpn_external_api_ip = vpn_info["external_api_ip"],
        self.vpn_tunnel_bearing_ip = vpn_info["tunnel_bearing_ip"]

    def cloud_uninstall(self):
        self.uninstall_cascaded()
        self.uninstall_vpn()
        self.uninstall_gateway()
        self.uninstall_network()
        self.release_ext_net_eip()

    def uninstall_cascaded(self):
        if self.cascaded_eip_public_ip is not None:
            self.installer.disassociate_elastic_address(
                    self.cascaded_eip_public_ip)
            self.installer.release_elastic_address(
                    self.cascaded_eip_allocation_id)
            self.cascaded_eip_public_ip = None
            self.cascaded_eip_allocation_id = None

        if self.cascaded_vm_id is not None:
            self.installer.terminate_instance(self.cascaded_vm_id)
            self.cascaded_vm_id = None

    def uninstall_gateway(self):
        if self.gateway_id is not None:
            self.installer.detach_internet_gateway(self.gateway_id, self.vpc_id)
            self.installer.delete_internet_gateway(self.gateway_id)
            self.gateway_id = None

    def uninstall_network(self):
        if self.debug_subnet_id is not None:
            self.installer.delete_subnet(self.debug_subnet_id)
            self.debug_subnet_id = None

        if self.base_subnet_id is not None:
            self.installer.delete_subnet(self.base_subnet_id)
            self.base_subnet_id = None

        if self.api_subnet_id is not None:
            self.installer.delete_subnet(self.api_subnet_id)
            self.api_subnet_id = None

        if self.tunnel_subnet_id is not None:
            self.installer.delete_subnet(self.tunnel_subnet_id)
            self.tunnel_subnet_id = None

        if self.vpc_id is not None:
            self.installer.delete_vpc(self.vpc_id)
            self.vpc_id = None

    def release_ext_net_eip(self):
        if not self.ext_net_eips:
            return

        for (elastic_ip, allocation_id) in self.ext_net_eips.items():
            try:
                self.installer.release_elastic_address(allocation_id)
            except:
                continue
        self.ext_net_eips = {}

    def uninstall_vpn(self):
        if self.vpn_eip_allocation_id is not None:
            self.installer.disassociate_elastic_address(
                    self.vpn_eip_public_ip)
            self.installer.release_elastic_address(
                    self.vpn_eip_allocation_id)
            self.vpn_eip_public_ip = None
            self.vpn_eip_allocation_id = None

        if self.vpn_vm_id is not None:
            self.installer.terminate_instance(self.vpn_vm_id)
            self.vpn_vm_id = None

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
            "external_api_ip": self.cascaded_api_ip,
            "tunnel_bearing_ip": self.cascaded_tunnel_ip,
            "internal_base_ip": self.cascaded_base_ip,
            "domain": self._distribute_cloud_domain(
                     self.cloud_params["project_info"]['region'], self.cloud_params['azname'], "--hws"),
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
                "access": self.cloud_params["access"],
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

    def get_cloud_info(self):
        cloud_info = self.cloud_info_handler.read_cloud_info()
        return cloud_info


    def add_route(self, subnet_type, cidr):
        if subnet_type == "api":
            self.installer.create_route(
                    self.rtb_id, cidr,
                    interface_id=self.vpn_api_interface_id)
            return
        if subnet_type == "tunnel":
            self.installer.create_route(
                    self.rtb_id, cidr,
                    interface_id=self.vpn_tunnel_interface_id)
            return

