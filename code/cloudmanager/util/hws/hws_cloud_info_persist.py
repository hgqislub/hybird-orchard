_access_cloud_install_info_file = os.path.join("/home/hybrid_cloud/data/hws/",
                             'hws_access_cloud_install.data')
from conf_util import *
class HWSCloudInfoPersist:
    def __init__(self, cloud_id):
        self.install_info_handler = CloudInfoHandler(_access_cloud_install_info_file, cloud_id)

    def write_vpc_info(cloud_id, vpc_id ,
                                api_subnet_cidr ,
                                tunnel_gw ,
                                tunnel_subnet_cidr):
        vpc_info = {
            "vpc_id": vpc_id
            "external_api_info":
            "tunnel_bearing_info":

        }
    vdc_network_info = {
                "api_gw": api_gw,
                "api_subnet_cidr": api_subnet_cidr,
                "tunnel_gw": tunnel_gw,
                "tunnel_subnet_cidr": tunnel_subnet_cidr
                }
    _write_unit_info(cloud_id, "vdc_network", vdc_network_info)


def write_cascaded(cloud_id,public_ip_api_reverse,
                                    public_ip_api_forward,
                                    public_ip_ntp_server,
                                    public_ip_ntp_client,
                                    public_ip_cps_web,
                                    cascaded_base_ip,
                                    cascaded_api_ip,
                                    cascaded_tunnel_ip):
    cascaded_info = {"public_ip_api_reverse": public_ip_api_reverse,
                     "public_ip_api_forward": public_ip_api_forward,
                     "public_ip_ntp_server": public_ip_ntp_server,
                     "public_ip_ntp_client": public_ip_ntp_client,
                     "public_ip_cps_web": public_ip_cps_web,
                     "cascaded_base_ip": cascaded_base_ip,
                     "cascaded_api_ip": cascaded_api_ip,
                     "cascaded_tunnel_ip": cascaded_tunnel_ip
                    }

    _write_unit_info(cloud_id, "cascaded", cascaded_info)


def write_vpn(cloud_id, public_ip_vpn,
                        vpn_api_ip,
                        vpn_tunnel_ip):
    vpn_info = {"public_ip_vpn": public_ip_vpn,
                "vpn_api_ip": vpn_api_ip,
                "vpn_tunnel_ip": vpn_tunnel_ip}

    _write_unit_info(cloud_id, "vpn", vpn_info)


def write_ext_net_eip(cloud_id, ext_net_eips):
    _write_unit_info(cloud_id, "ext_net_eips", ext_net_eips)