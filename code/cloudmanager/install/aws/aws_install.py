
from heat.openstack.common import log as logging

import heat.engine.resources.cloudmanager.util.conf_util as conf_util
from heat.engine.resources.cloudmanager.util.subnet_manager import SubnetManager
from heat.engine.resources.cloudmanager.util.cloud_manager_exception import *
import heat.engine.resources.cloudmanager.util.proxy_manager as proxy_manager
import heat.engine.resources.cloudmanager.util.constant as constant
from region_mapping import *
import aws_util
import aws_access_cloud_data_handler as data_handler

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

        self.installer = aws_util.AWSInstaller(access_key,
                                               secret_key, self.region, self.az)

        self._read_default_conf()
        self.cascaded_image = self.default_cascaded_image
        self.cascaded_vm_type = self.default_cascaded_flavor
        self.vpn_image = self.default_vpn_image
        self.vpn_vm_type = self.default_vpn_flavor
        self.hynode_image = self.default_hynode_image
        self.v2v_image = self.default_v2v_image
        self.v2v_vm_type = self.default_v2v_flavor
        self.ceph_image = self.default_ceph_image
        self.ceph_vm_type = self.default_ceph_flavor

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

    def _read_default_conf(self):
        try:
            self.default_params = conf_util.read_conf(constant.Cascading.AWS_CONF_FILE)
            image_info = self.default_params["image"]
            self.default_cascaded_image = image_info["cascaded_image"]
            self.default_cascaded_flavor = image_info["cascaded_flavor"]
            self.default_vpn_image = image_info["vpn_image"]
            self.default_vpn_flavor = image_info["vpn_flavor"]
            self.default_v2v_image =  image_info["v2v_image"]
            self.default_v2v_flavor =  image_info["v2v_flavor"]
            self.default_ceph_image = image_info["ceph_image"]
            self.default_ceph_flavor = image_info["ceph_flavor"]
            self.default_hynode_image = image_info["hynode_image"]

            network = self.default_params["network"]
            self.default_vpc_cidr = network["vpc_cidr"]
            self.default_external_api_cidr = network["external_api_cidr"]
            self.default_tunnel_bearing_cidr = network["tunnel_bearing_cidr"]
            self.default_internal_base_cidr = network["internal_base_cidr"]
            self.default_debug_cidr = network["debug_cidr"]

        except IOError as e:
            error = "read file = %s error" % constant.Cascading.ENV_FILE
            LOG.error(e)
            raise ReadEnvironmentInfoFailure(error = error)
        except KeyError as e:
            error = "read key = %s error in file = %s" % (e.message, _environment_conf)
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
        self.ceph_subnet_cidr = None
        self.ceph_subnet_id = None
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

        self.v2v_vm_id = None
        self.v2v_ip = None

        self.hynode_image_id = None

        self.ceph_deploy_vm_id = None
        self.ceph_deploy_ip = None
        self.ceph_deploy_interface_id = None

        self.ceph_node1_vm_id = None
        self.ceph_node1_ip = None
        self.ceph_node1_interface_id = None

        self.ceph_node2_vm_id = None
        self.ceph_node2_ip = None
        self.ceph_node2_interface_id = None

        self.ceph_node3_vm_id = None
        self.ceph_node3_ip = None
        self.ceph_node3_interface_id = None

        self.ext_net_eips = {}

        cloud_info = data_handler.get_aws_access_cloud(self.cloud_id)
        if not cloud_info:
            return

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
            self.ceph_subnet_cidr = vpc_info["ceph_subnet_cidr"]
            self.ceph_subnet_id = vpc_info["ceph_subnet_id"]
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

        if "v2v_gateway" in cloud_info.keys():
            v2v_info = cloud_info["v2v_gateway"]
            self.v2v_vm_id = v2v_info["vm_id"]
            self.v2v_ip = v2v_info["ip"]

        if "hynode" in cloud_info.keys():
            hynode_info = cloud_info["hynode"]
            self.hynode_image_id = hynode_info["image_id"]

        if "ceph_cluster" in cloud_info.keys():
            ceph_cluster_info = cloud_info["ceph_cluster"]
            self.ceph_deploy_vm_id = ceph_cluster_info["deploy_vm_id"]
            self.ceph_deploy_ip = ceph_cluster_info["deploy_ip"]
            self.ceph_node1_vm_id = ceph_cluster_info["node1_vm_id"]
            self.ceph_node1_ip = ceph_cluster_info["node1_ip"]
            self.ceph_node2_vm_id = ceph_cluster_info["node2_vm_id"]
            self.ceph_node2_ip = ceph_cluster_info["node2_ip"]
            self.ceph_node3_vm_id = ceph_cluster_info["node3_vm_id"]
            self.ceph_node3_ip = ceph_cluster_info["node3_ip"]

        if "ext_net_eips" in cloud_info.keys():
            self.ext_net_eips = cloud_info["ext_net_eips"]

    def install_vpc(self, vpc_cidr, debug_cidr, base_cidr,
                    api_cidr, tunnel_cidr, ceph_cidr, green_ips):
        if self.vpc_id:
            return

        # install vpc
        vpc = self.installer.create_vpc(vpc_cidr)
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
        self.debug_subnet_cidr = debug_cidr
        self.debug_subnet_id = self.installer.create_subnet(self.vpc_id,
                                                            debug_cidr)
        self.base_subnet_cidr = base_cidr
        self.base_subnet_id = self.installer.create_subnet(self.vpc_id,
                                                           base_cidr)
        self.api_subnet_cidr = api_cidr
        self.api_subnet_id = self.installer.create_subnet(self.vpc_id,
                                                          api_cidr)
        self.tunnel_subnet_cidr = tunnel_cidr
        self.tunnel_subnet_id = self.installer.create_subnet(self.vpc_id,
                                                             tunnel_cidr)
        self.ceph_subnet_cidr = ceph_cidr
        self.ceph_subnet_id = self.api_subnet_id

        for ip in green_ips:
            self.add_security("%s/32" % ip)

        data_handler.write_vpc(self.cloud_id,
                               self.vpc_id,
                               self.debug_subnet_cidr, self.debug_subnet_id,
                               self.base_subnet_cidr, self.base_subnet_id,
                               self.api_subnet_cidr, self.api_subnet_id,
                               self.tunnel_subnet_cidr, self.tunnel_subnet_id,
                               self.ceph_subnet_cidr, self.ceph_subnet_id,
                               self.gateway_id, self.rtb_id)

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
            public_ip_name = self.cloud_params["azname"]+"_vpn_public_ip"
            result = self.installer.alloc_public_ip(public_ip_name)
            self.vpn_public_ip = result["public_ip_address"]
            self.vpn_public_ip_id = result["id"]

            self.install_data_handler.write_public_ip_info(
                self.vpn_public_ip,
                self.vpn_public_ip_id
                )

    def _alloc_cascaded_public_ip(self):
        if self.cascaded_public_ip_id is None:
            public_ip_name = self.cloud_params["azname"]+"_cascaded_public_ip"
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
        self._cloud_preinstall()

    def _cloud_preinstall(self):
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

        self.cascaded_internal_base_ip = self._alloc_cascaded_ip(self.internal_base_cidr, "12")
        self.cascaded_tunnel_bearing_ip = self._alloc_cascaded_ip(self.tunnel_bearing_cidr, "4")
        self.cascaded_external_api_ip = self._alloc_cascaded_ip(self.external_api_cidr, "4")
        self.cascaded_debug_ip = self._alloc_cascaded_ip(self.debug_cidr, "4")


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
        vpn_info = self.cloud_params["vpn_info"]
        if vpn_info and vpn_info["exist"] == "true":
            self._read_exist_vpn_info()
        else:
            self._install_vpn()
        self._install_cascaded()

    def _read_exist_vpn_info(self):
        vpn_info = self.cloud_params["vpn_info"]
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
        nics = [{"subnet_id": self.debug_id,
                 "ip_address": self.cascaded_debug_ip}]
        security_groups = [self.security_group_id]
        server_name = self.cloud_params["azname"]+"_cascaded"
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
        server_name = self.cloud_params["azname"]+"_vpn"
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
        self.vpc_cidr = None
        self.external_api_cidr = None
        self.tunnel_bearing_cidr = None
        self.internal_base_cidr = None
        self.debug_cidr = None

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




