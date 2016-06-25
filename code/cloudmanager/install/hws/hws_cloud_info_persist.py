from heat.engine.resources.cloudmanager.util.conf_util import CloudInfoHandler


class HwsCloudInfoPersist:
    def __init__(self, _access_cloud_install_info_file, cloud_id):
        self.info_handler = CloudInfoHandler(_access_cloud_install_info_file, cloud_id)

    def write_vpc_info(self, vpc_id, vpc_name, vpc_cidr, security_group_id):
        vpc_info = {
            "id": vpc_id,
            "name": vpc_name,
            "cidr": vpc_cidr,
            "security_group_id": security_group_id
        }
        self.info_handler.write_unit_info("vpc", vpc_info)

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
    def write_subnets_info(self, external_api_subnet, tunnel_bearing_subnet, internal_base_subnet, debug_subnet):
        subnets_info = {
            "external_api": external_api_subnet,
            "tunnel_bearing": tunnel_bearing_subnet,
            "internal_base": internal_base_subnet,
            "debug": debug_subnet
        }
        self.info_handler.write_unit_info("subnets", subnets_info)

    def write_cascaded_info(self, server_id, public_ip,
                            external_api_ip,tunnel_bearing_ip,
                  tunnel_bearing_nic_id, external_api_nic_id,
                    internal_base_nic_id, port_id_bind_public_ip):
        cascaded_info = {"server_id": server_id,
                    "public_ip": public_ip,
                    "external_api_ip": external_api_ip,
                    "tunnel_bearing_ip": tunnel_bearing_ip,
                    "tunnel_bearing_nic_id":tunnel_bearing_nic_id,
                    "external_api_nic_id":external_api_nic_id,
                    "internal_base_nic_id":internal_base_nic_id,
                    "port_id_bind_public_ip":port_id_bind_public_ip

                    }

        self.info_handler.write_unit_info("cascaded", cascaded_info)

    def write_public_ip_info(self, vpn_public_ip,
                             vpn_public_ip_id,
                             cascaded_public_ip=None,
                             cascaded_public_ip_id=None):
        public_ip_info = {
            "vpn_public_ip": vpn_public_ip,
            "vpn_public_ip_id": vpn_public_ip_id,
            "cascaded_public_ip": cascaded_public_ip,
            "cascaded_public_ip_id": cascaded_public_ip_id
        }
        self.info_handler.write_unit_info("public_ip", public_ip_info)

    def write_vpn(self, server_id, public_ip, external_api_ip, tunnel_bearing_ip):
        vpn_info = {"server_id": server_id,
                "public_ip": public_ip,
                "external_api_ip": external_api_ip,
                "tunnel_bearing_ip": tunnel_bearing_ip}

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