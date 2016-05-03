
from conf_util import *
class HWSCloudInfoPersist:
    def __init__(self, _access_cloud_install_info_file, cloud_id):
        self.info_handler = CloudInfoHandler(_access_cloud_install_info_file, cloud_id)

    def write_vpc_info(self, vpc_id, vpc_name, vpc_cidr):
        vpc_info = {
            "id": vpc_id,
            "name": vpc_name,
            "cidr": vpc_cidr
        }
        self.info_handler.write_unit_info("vpc", vpc_info)

    def write_subnets_info(self, external_api_subnet, tunnel_bearing_subnet, internal_base_subnet, debug_subnet):
        subnets_info = {
            "external_api": external_api_subnet,
            "tunnel_bearing": tunnel_bearing_subnet,
            "internal_base": internal_base_subnet,
            "debug": debug_subnet
        }
        self.info_handler.write_unit_info("subnets", subnets_info)

    def write_cascaded_info(self, server_id, external_api_ip,tunnel_bearing_ip):
        cascaded_info = {"server_id": server_id,
                     "external_api_ip": external_api_ip,
                     "tunnel_bearing_ip": tunnel_bearing_ip
                    }

        self.info_handler.write_unit_info("cascaded", cascaded_info)


    def write_vpn(self, server_id, public_ip, external_api_ip, tunnel_bearing_ip):
        vpn_info = {"server_id": server_id,
                "public_ip": public_ip,
                "external_api_ip": external_api_ip,
                "tunnel_bearing_ip": tunnel_bearing_ip}

        self.info_handler.write_unit_info("vpn", vpn_info)


    def write_ext_net_eip(self, ext_net_eips):
        self.info_handler.write_unit_info("ext_net_eips", ext_net_eips)

    def write_cloud_info(self, data):
        self.info_handler.write_cloud_info(data)