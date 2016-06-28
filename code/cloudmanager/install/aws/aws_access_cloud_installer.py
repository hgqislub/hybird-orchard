# -*- coding:utf-8 -*-

__author__ = 'q00222219@huawei'

import json
import os

from heat.openstack.common import log as logger

import aws_access_cloud_data_handler as data_handler
import aws_util

_install_conf = os.path.join("/home/hybrid_cloud/conf",
                             'aws_access_cloud_install.conf')


def _read_install_conf():
    if not os.path.exists(_install_conf):
        logger.error("read %s : No such file." % _install_conf)
        return None
    with open(_install_conf, 'r+') as fd:
        tmp = fd.read()
        return json.loads(tmp)

class AWSCascadedInstaller(object):
    def __init__(self, cloud_id, access_key=None, secret_key=None,
                 region=None, az=None):
        self.cloud_id = cloud_id
        self.region = region
        self.az = az
        self.access_key = access_key
        self.secret_key = secret_key
        self.installer = aws_util.AWSInstaller(access_key,
                                               secret_key, region,
                                               az)

        install_conf = _read_install_conf()

        self.cascaded_image = install_conf["cascaded_image"]
        self.cascaded_vm_type = install_conf["cascaded_vm_type"]
        self.vpn_image = install_conf["vpn_image"]
        self.vpn_vm_type = install_conf["vpn_vm_type"]
        self.hynode_image = install_conf["hynode_image"]
        self.v2v_image = install_conf["v2v_image"]
        self.v2v_vm_type = install_conf["v2v_vm_type"]
        self.ceph_image = install_conf["ceph_image"]
        self.ceph_vm_type = install_conf["ceph_vm_type"]

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

        self._read_aws_access_cloud()

    def _read_aws_access_cloud(self):
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

    def _get_cascaded_ip(self, debug_cidr_block, base_cidr_block,
                         api_cidr_block, tunnel_cidr_block):
        ip_list = debug_cidr_block.split(".")
        self.cascaded_debug_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], "12"])

        ip_list = base_cidr_block.split(".")
        self.cascaded_base_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], "12"])

        ip_list = api_cidr_block.split(".")
        self.cascaded_api_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], "150"])

        ip_list = tunnel_cidr_block.split(".")
        self.cascaded_tunnel_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], "12"])

    def _get_vpn_ip(self, api_cidr_block, tunnel_cidr_block):
        ip_list = api_cidr_block.split(".")
        self.vpn_api_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], "254"])

        ip_list = tunnel_cidr_block.split(".")
        self.vpn_tunnel_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], "254"])

    def _get_v2v_ip(self, api_cidr_block):
        ip_list = api_cidr_block.split(".")
        self.v2v_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], "253"])

    def _get_ceph_cluster_ip(self, ceph_cidr_block):
        ip_list = ceph_cidr_block.split(".")
        self.ceph_deploy_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], "249"])

        self.ceph_node1_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], "250"])

        self.ceph_node2_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], "251"])

        self.ceph_node3_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], "252"])

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

    def install_cascaded(self, debug_cidr_block, base_cidr_block,
                         api_cidr_block, tunnel_cidr_block):
        if self.cascaded_vm_id:
            return

        # install cascaded vm
        self._get_cascaded_ip(debug_cidr_block, base_cidr_block,
                              api_cidr_block, tunnel_cidr_block)
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

        data_handler.write_cascaded(self.cloud_id,
                                    self.cascaded_vm_id,
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

    def install_vpn(self, api_cidr_block, tunnel_cidr_block,
                    local_api_cidr, local_tunnel_cidr):
        if self.vpn_vm_id:
            return

        # install vpn vm
        self._get_vpn_ip(api_cidr_block, tunnel_cidr_block)
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

        self.add_route("api", local_api_cidr)
        self.add_route("tunnel", local_tunnel_cidr)

        data_handler.write_vpn(self.cloud_id,
                               self.vpn_vm_id,
                               self.vpn_eip_public_ip,
                               self.vpn_eip_allocation_id,
                               self.vpn_api_ip, self.vpn_tunnel_ip,
                               self.vpn_api_interface_id,
                               self.vpn_tunnel_interface_id)

    def install_v2v_gateway(self, api_cidr_block):
        if self.v2v_vm_id:
            return

        # install v2v gateway
        self._get_v2v_ip(api_cidr_block)
        v2v_en = aws_util.AWSInterface(self.api_subnet_id, self.v2v_ip)

        v2v_vm = self.installer.create_vm(self.v2v_image,
                                          self.v2v_vm_type,
                                          v2v_en)
        self.v2v_vm_id = v2v_vm.id

        data_handler.write_v2v_gateway(self.cloud_id,
                                       self.v2v_vm_id, self.v2v_ip)

    def install_ceph_cluster(self, api_cidr_block):
        if self.ceph_node1_ip:
            return

        # install ceph cluster
        self._get_ceph_cluster_ip(api_cidr_block)
        ceph_deploy_en = aws_util.AWSInterface(
                self.ceph_subnet_id, self.ceph_deploy_ip)
        ceph_deploy_vm = self.installer.create_vm(
                self.ceph_image, self.ceph_vm_type, ceph_deploy_en)

        self.ceph_deploy_vm_id = ceph_deploy_vm.id

        ceph_node1_en = aws_util.AWSInterface(
                self.ceph_subnet_id, self.ceph_node1_ip)
        ceph_node1_vm = self.installer.create_vm(
                self.ceph_image, self.ceph_vm_type, ceph_node1_en)
        self.ceph_node1_vm_id = ceph_node1_vm.id

        ceph_node2_en = aws_util.AWSInterface(
                self.ceph_subnet_id, self.ceph_node2_ip)
        ceph_node2_vm = self.installer.create_vm(
                self.ceph_image, self.ceph_vm_type, ceph_node2_en)
        self.ceph_node2_vm_id = ceph_node2_vm.id

        ceph_node3_en = aws_util.AWSInterface(
                self.ceph_subnet_id, self.ceph_node3_ip)
        ceph_node3_vm = self.installer.create_vm(
                self.ceph_image, self.ceph_vm_type, ceph_node3_en)
        self.ceph_node3_vm_id = ceph_node3_vm.id

        data_handler.write_ceph_cluster(
                self.cloud_id,
                self.ceph_deploy_vm_id, self.ceph_deploy_ip,
                self.ceph_node1_vm_id, self.ceph_node1_ip,
                self.ceph_node2_vm_id, self.ceph_node2_ip,
                self.ceph_node3_vm_id, self.ceph_node3_ip)

    def query_hynode_image_id(self):
        if self.hynode_image_id:
            return

        if not self.hynode_image:
            self.hynode_image_id = self.installer.query_image_id(
                    self.hynode_image)
            data_handler.write_hynode(self.cloud_id, self.hynode_image_id)

    def allocate_ext_net_eip(self):
        if self.ext_net_eips:
            return

        first_eip = None
        try:
            first_eip = self.installer.allocate_elastic_address()
        except Exception as e:
            logger.error("allocate elastic address error, check the account. "
                         "error: %s" % e.message)

        if not first_eip:
            logger.error("allocate elastic address error, check the account.")

        self.ext_net_eips[first_eip.public_ip] = first_eip.allocation_id
        fist_8bit = first_eip.public_ip.split('.')[0]

        while True:
            try:
                eip = self.installer.allocate_elastic_address()
                fist_8bit_ip = eip.public_ip.split('.')[0]
                if fist_8bit == fist_8bit_ip:
                    self.ext_net_eips[eip.public_ip] = eip.allocation_id
                else:
                    self.installer.release_elastic_address(eip.public_ip)
            except:
                break

        data_handler.write_ext_net_eip(
                cloud_id=self.cloud_id, ext_net_eips=self.ext_net_eips)

    def package_aws_access_cloud_info(self):
        if not self.vpc_id:
            return None

        info = {"vpc":
                    {"vpc_id": self.vpc_id,
                     "debug_subnet_cidr": self.debug_subnet_cidr,
                     "debug_subnet_id": self.debug_subnet_id,
                     "base_subnet_cidr": self.base_subnet_cidr,
                     "base_subnet_id": self.base_subnet_id,
                     "api_subnet_cidr": self.api_subnet_cidr,
                     "api_subnet_id": self.api_subnet_id,
                     "tunnel_subnet_cidr": self.tunnel_subnet_cidr,
                     "tunnel_subnet_id": self.tunnel_subnet_id,
                     "ceph_subnet_cidr": self.ceph_subnet_cidr,
                     "ceph_subnet_id": self.ceph_subnet_id,
                     "gateway_id": self.gateway_id,
                     "rtb_id": self.rtb_id},
                "cascaded":
                    {"vm_id": self.cascaded_vm_id,
                     "debug_ip": self.cascaded_debug_ip,
                     "debug_interface_id": self.cascaded_debug_interface_id,
                     "base_ip": self.cascaded_base_ip,
                     "base_interface_id": self.cascaded_base_interface_id,
                     "api_ip": self.cascaded_api_ip,
                     "api_interface_id": self.cascaded_api_interface_id,
                     "tunnel_ip": self.cascaded_tunnel_ip,
                     "tunnel_interface_id": self.cascaded_tunnel_interface_id,
                     "eip_public_ip": self.cascaded_eip_public_ip,
                     "eip_allocation_id": self.cascaded_eip_allocation_id},
                "vpn":
                    {"vm_id": self.vpn_vm_id,
                     "api_ip": self.vpn_api_ip,
                     "api_interface_id": self.vpn_api_interface_id,
                     "tunnel_ip": self.vpn_tunnel_ip,
                     "tunnel_interface_id": self.vpn_tunnel_interface_id,
                     "eip_public_ip": self.vpn_eip_public_ip,
                     "eip_allocation_id": self.vpn_eip_allocation_id},
                "ceph_cluster":
                    {"deploy_vm_id": self.ceph_deploy_vm_id,
                     "deploy_ip": self.ceph_deploy_ip,
                     "node1_vm_id": self.ceph_node1_vm_id,
                     "node1_ip": self.ceph_node1_ip,
                     "node2_vm_id": self.ceph_node2_vm_id,
                     "node2_ip": self.ceph_node2_ip,
                     "node3_vm_id": self.ceph_node3_vm_id,
                     "node3_ip": self.ceph_node3_ip},
                "v2v_gateway":
                    {"vm_id": self.v2v_vm_id,
                     "ip": self.v2v_ip},
                "hynode":
                    {"ami_id": self.hynode_image_id},
                "ext_net_eips": self.ext_net_eips.keys()}
        return info

    def rollback(self):
        if self.cascaded_eip_public_ip is not None:
            self.installer.disassociate_elastic_address(
                    self.cascaded_eip_public_ip)
            self.installer.release_elastic_address(
                    self.cascaded_eip_allocation_id)
            self.cascaded_eip_public_ip = None
            self.cascaded_eip_allocation_id = None

        if self.vpn_eip_allocation_id is not None:
            self.installer.disassociate_elastic_address(
                    self.vpn_eip_public_ip)
            self.installer.release_elastic_address(
                    self.vpn_eip_allocation_id)
            self.vpn_eip_public_ip = None
            self.vpn_eip_allocation_id = None

        if self.cascaded_vm_id is not None:
            self.installer.terminate_instance(self.cascaded_vm_id)
            self.cascaded_vm_id = None

        if self.vpn_vm_id is not None:
            self.installer.terminate_instance(self.vpn_vm_id)
            self.vpn_vm_id = None

        if self.v2v_vm_id is not None:
            self.installer.terminate_instance(self.v2v_vm_id)
            self.v2v_vm_id = None

        if self.ceph_deploy_vm_id is not None:
            self.installer.terminate_instance(self.ceph_deploy_vm_id)
            self.ceph_deploy_vm_id = None

        if self.ceph_node1_vm_id is not None:
            self.installer.terminate_instance(self.ceph_node1_vm_id)
            self.ceph_node1_vm_id = None

        if self.ceph_node2_vm_id is not None:
            self.installer.terminate_instance(self.ceph_node2_vm_id)
            self.ceph_node2_vm_id = None

        if self.ceph_node3_vm_id is not None:
            self.installer.terminate_instance(self.ceph_node3_vm_id)
            self.ceph_node3_vm_id = None

        if self.gateway_id is not None:
            self.installer.detach_internet_gateway(self.gateway_id, self.vpc_id)
            self.installer.delete_internet_gateway(self.gateway_id)
            self.gateway_id = None

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

        self.release_ext_net_eip()
        data_handler.delete_aws_access_cloud(self.cloud_id)

    def uninstall(self):
        self._read_aws_access_cloud()
        self.rollback()

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

    def add_security(self, cidr):
        sgs = self.installer.get_all_security_groups(self.vpc_id)
        for sg in sgs:
            sg.authorize(ip_protocol="-1", cidr_ip=cidr)

    def remove_security(self, cidr):
        sgs = self.installer.get_all_security_groups(self.vpc_id)
        for sg in sgs:
            sg.revoke(ip_protocol="-1", cidr_ip=cidr)

    def release_ext_net_eip(self):
        if not self.ext_net_eips:
            return

        for (elastic_ip, allocation_id) in self.ext_net_eips.items():
            try:
                self.installer.release_elastic_address(allocation_id)
            except:
                continue
        self.ext_net_eips = {}


def aws_access_cloud_install(cloud_id, region, az, access_key, secret_key,
                             vpc_cidr="172.29.0.0/16",
                             debug_cidr="172.29.16.0/20",
                             base_cidr="172.29.124.0/20",
                             api_cidr="172.29.0.0/24",
                             tunnel_cidr="172.29.128.0/24",
                             ceph_cidr="172.29.0.0/24",
                             green_ips=["205.177.226.131"],
                             local_api_cidr="162.3.0.0/16",
                             local_tunnel_cidr="172.28.48.0/20",
                             agentless=False, install_ceph=True):
    installer = None
    try:
        # import pdb
        # pdb.set_trace()
        installer = AWSCascadedInstaller(cloud_id, access_key, secret_key,
                                         region, az)
        installer.install_vpc(vpc_cidr, debug_cidr, base_cidr, api_cidr,
                              tunnel_cidr, ceph_cidr, green_ips)

        installer.install_cascaded(debug_cidr, base_cidr, api_cidr, tunnel_cidr)
        installer.install_vpn(api_cidr, tunnel_cidr,
                              local_api_cidr, local_tunnel_cidr)
        installer.install_v2v_gateway(api_cidr)

        if agentless:
            installer.query_hynode_image_id()

        if install_ceph:
            installer.install_ceph_cluster(api_cidr)

        installer.allocate_ext_net_eip()

        return installer.package_aws_access_cloud_info()
    except Exception as e:
        logger.error("aws cascaded install error, error: %s" % e.message)
        if installer is not None:
            installer.rollback()


def aws_access_cloud_uninstall(cloud_id, region, az, access_key, secret_key):
    try:
        installer = AWSCascadedInstaller(cloud_id, access_key, secret_key,
                                         region, az)
        installer.uninstall()
    except Exception as e:
        logger.error("aws cascaded uninstall error, error: %s" % e.message)


def aws_access_cloud_add_route(cloud_id, region, az, access_key, secret_key,
                               type="tunnel", cidr="172.28.48.0/20"):
    installer = AWSCascadedInstaller(cloud_id, access_key, secret_key,
                                     region, az)
    installer.add_route(type, cidr)


def aws_access_cloud_add_security(cloud_id, region, az, access_key, secret_key,
                                  cidr="205.177.226.131/32"):
    installer = AWSCascadedInstaller(cloud_id, access_key, secret_key,
                                     region, az)
    installer.add_security(cidr)


def aws_access_cloud_remove_security(cloud_id, region, az, access_key, secret_key,
                                     cidr="205.177.226.131/32"):
    installer = AWSCascadedInstaller(cloud_id, access_key, secret_key,
                                     region, az)
    installer.remove_security(cidr)


def get_aws_access_cloud_install_info(cloud_id):
    installer = AWSCascadedInstaller(cloud_id)
    return installer.package_aws_access_cloud_info()


def allocate_ext_net_eip(cloud_id, region, az, access_key, secret_key):
    installer = AWSCascadedInstaller(cloud_id, access_key, secret_key,
                                     region, az)
    installer.allocate_ext_net_eip()
    return installer.ext_net_eips.keys()


def release_ext_net_eip(cloud_id, region, az, access_key, secret_key):
    installer = AWSCascadedInstaller(cloud_id, access_key, secret_key,
                                     region, az)
    return installer.release_ext_net_eip()

