from heat.engine.resources.cloudmanager.util.conf_util import *


class VcloudCloudInfoPersist:
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

    def write_subnets_cidr(self,
                           external_api_cidr,
                           tunnel_bearing_cidr,
                           internal_base_cidr,
                           internal_base_name,
                           tunnel_bearing_name,
                           external_api_name
                        ):
        subnets_cidr_info = {
            "external_api_cidr": external_api_cidr,
            "tunnel_bearing_cidr": tunnel_bearing_cidr,
            "internal_base_cidr": internal_base_cidr,
            "internal_base_name": internal_base_name,
            "tunnel_bearing_name": tunnel_bearing_name,
            "external_api_name": external_api_name
        }
        self.info_handler.write_unit_info("subnets_cidr", subnets_cidr_info)

    def write_subnets_info(self, internal_base_existed, tunnel_bearing_existed, external_api_existed):
        subnets_info = {
            "internal_base_existed" : internal_base_existed,
            "tunnel_bearing_existed" :  tunnel_bearing_existed,
            "external_api_existed" : external_api_existed

        }
        self.info_handler.write_unit_info("subnets", subnets_info)

    def write_cascaded_info(self, cascaded_vm_created):
        cascaded_info = {
                         'cascaded_vm_created' : cascaded_vm_created

                    }

        self.info_handler.write_unit_info("cascaded", cascaded_info)

    def write_cascaded_public_ip(self, public_ip_api_reverse,
                                    public_ip_api_forward,
                                    public_ip_ntp_server,
                                    public_ip_ntp_client,
                                    public_ip_cps_web):
        cascaded_public_ip = {
                         'public_ip_api_reverse' : public_ip_api_reverse,
            'public_ip_api_forward' : public_ip_api_forward,
            'public_ip_ntp_server' : public_ip_ntp_server,
            'public_ip_ntp_client' : public_ip_ntp_client,
            'public_ip_cps_web' : public_ip_cps_web
                    }

        self.info_handler.write_unit_info("cascaded_public_ip", cascaded_public_ip)


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

    def write_vpn(self, cascaded_vpn_vm_created):
        vpn_info = {'cascaded_vpn_vm_created' : cascaded_vpn_vm_created}

        self.info_handler.write_unit_info("vpn", vpn_info)

    def write_vpn_public_ip(self, vpn_public_ip):

        vpn_public_ip = {
                         'vpn_public_ip' : vpn_public_ip
                        }
        self.info_handler.write_unit_info("vpn_public_ip", vpn_public_ip)

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