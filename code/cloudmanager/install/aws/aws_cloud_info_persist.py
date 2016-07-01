# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import threading

from awscloud import AwsCloud
from heat.engine.resources.cloudmanager.util.commonutils import *
from heat.engine.resources.cloudmanager.util.conf_util import CloudInfoHandler

def aws_cloud_2_dict(obj):
    result = {}
    result.update(obj.__dict__)
    return result


def dict_2_aws_cloud(aws_dict):
    aws_cloud = AwsCloud(cloud_id=aws_dict["cloud_id"],
                         access_key=aws_dict["access_key"],
                         secret_key=aws_dict["secret_key"],
                         region_name=aws_dict["region_name"],
                         az=aws_dict["az"],
                         az_alias=aws_dict["az_alias"],
                         cascaded_domain=aws_dict["cascaded_domain"],
                         cascaded_eip=aws_dict["cascaded_eip"],
                         vpn_eip=aws_dict["vpn_eip"],
                         cloud_proxy=aws_dict["cloud_proxy"],
                         driver_type=aws_dict["driver_type"],
                         access=aws_dict["access"],
                         with_ceph=aws_dict["with_ceph"])
    return aws_cloud

class AwsCloudInfoPersist(object):
    def __init__(self, _access_cloud_install_info_file, cloud_id):
        self.info_handler = CloudInfoHandler(_access_cloud_install_info_file, cloud_id)

    def write_vpc_info(self, vpc_id,
              debug_subnet_cidr, debug_subnet_id,
              base_subnet_cidr, base_subnet_id,
              api_subnet_id_cidr, api_subnet_id,
              tunnel_subnet_cidr, tunnel_subnet_id,
              gateway_id, rtb_id):
        vpc_info = {"vpc_id": vpc_id,
                "debug_subnet_cidr": debug_subnet_cidr,
                "debug_subnet_id": debug_subnet_id,
                "base_subnet_cidr": base_subnet_cidr,
                "base_subnet_id": base_subnet_id,
                "api_subnet_cidr": api_subnet_id_cidr,
                "api_subnet_id": api_subnet_id,
                "tunnel_subnet_cidr": tunnel_subnet_cidr,
                "tunnel_subnet_id": tunnel_subnet_id,
                "gateway_id": gateway_id,
                "rtb_id": rtb_id}
        self.info_handler.write_unit_info("vpc", vpc_info)

    def write_cascaded_info(self,
                   cascaded_vm_id,
                   cascaded_eip_public_ip, cascaded_eip_allocation_id,
                   cascaded_debug_ip, cascaded_debug_interface_id,
                   cascaded_base_ip, cascaded_base_interface_id,
                   cascaded_api_ip, cascaded_api_interface_id,
                   cascaded_tunnel_ip, cascaded_tunnel_interface_id):
        cascaded_info = {"vm_id": cascaded_vm_id,
                     "eip_public_ip": cascaded_eip_public_ip,
                     "eip_allocation_id": cascaded_eip_allocation_id,
                     "debug_ip": cascaded_debug_ip,
                     "debug_interface_id": cascaded_debug_interface_id,
                     "base_ip": cascaded_base_ip,
                     "base_interface_id": cascaded_base_interface_id,
                     "api_ip": cascaded_api_ip,
                     "api_interface_id": cascaded_api_interface_id,
                     "tunnel_ip": cascaded_tunnel_ip,
                     "tunnel_interface_id": cascaded_tunnel_interface_id}
        self.info_handler.write_unit_info("cascaded", cascaded_info)

    def write_subnets_cidr(self, vpc_cidr,
                           external_api_cidr,
                           tunnel_bearing_cidr,
                           internal_base_cidr,
                           debug_cidr):
        subnets_cidr_info = {
            "vpc_cidr": vpc_cidr,
            "external_api_cidr": external_api_cidr,
            "tunnel_bearing_cidr": tunnel_bearing_cidr,
            "internal_base_cidr": internal_base_cidr,
            "debug_cidr": debug_cidr
        }
        self.info_handler.write_unit_info("subnets_cidr", subnets_cidr_info)

    def write_vpn_info(self,
              vpn_vm_id,
              vpn_eip_public_ip, vpn_eip_allocation_id,
              vpn_api_ip, vpn_tunnel_ip,
              vpn_api_interface_id=None, vpn_tunnel_interface_id=None):
        vpn_info = {"vm_id": vpn_vm_id,
                "eip_public_ip": vpn_eip_public_ip,
                "eip_allocation_id": vpn_eip_allocation_id,
                "api_ip": vpn_api_ip,
                "tunnel_ip": vpn_tunnel_ip,
                "api_interface_id": vpn_api_interface_id,
                "tunnel_interface_id": vpn_tunnel_interface_id}

        self.info_handler.write_unit_info("vpn", vpn_info)

    def write_proxy(self, proxy_info):
        self.info_handler.write_unit_info("proxy_info", proxy_info)

    def read_proxy(self):
        return self.info_handler.get_unit_info("proxy_info")

    def write_cloud_info(self, data):
        self.info_handler.write_cloud_info(data)

    def read_cloud_info(self):
        return self.info_handler.read_cloud_info()

    def delete_cloud_info(self):
        self.info_handler.delete_cloud_info()

    def list_all_cloud_id(self):
        all_cloud = self.info_handler.get_all_unit_info()
        return all_cloud.keys()

    def get_cloud_info_with_id(self, cloud_id):
        all_cloud = self.info_handler.get_all_unit_info()
        if cloud_id in all_cloud.keys():
            return all_cloud[cloud_id]
