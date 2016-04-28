
import sys
sys.path.append('..')

from heat.openstack.common import log as logging
import cloudinfo_util as utils
import threading
import os
import json
import cloudmanager.region_mapping

_hws_access_cloud_data_file = os.path.join("/home/hybrid_cloud/data/hws",
                                           "hws_access_cloud_install.data")
_hws_access_cloud_data_file_lock = threading.Lock()

LOG=logging.getLogger(__name__)

class HwsCloudInfo(utils.CloudInfo):
    def __init__(self):

        self.cloud_id = None
        self.vcloud_url = None
        self.vcloud_org = None
        self.vcloud_vdc = None
        self.vcloud_edgegw = None
        self.username = None
        self.passwd = None
        self.region_name = None
        self.availabilityzone = None
        self.azname = None
        self.cascaded_domain = None
        self.cascaded_eip = None
        self.vpn_eip = None
        self.cloud_proxy = None
        self.driver_type = None
        self.access = None
        self.with_ceph = None

    def initialize(self, cloud_params, install_info, proxy_info, installer):
        self.cloud_id = "@".join([cloud_params['vcloud_url'],cloud_params['vcloud_org'],
                                  cloud_params['vcloud_vdc'], cloud_params['region_name'],
                                  cloud_params['azname']])

        self.cascaded_domain = installer._distribute_cloud_domain(
                region_name=cloud_params['region_name'], azname=cloud_params['azname'], az_tag="--vcloud")
        self.vcloud_url = cloud_params['vcloud_url']
        self.vcloud_org = cloud_params['vcloud_org']
        self.vcloud_vdc = cloud_params['vcloud_vdc']
        self.vcloud_edgegw = cloud_params['vcloud_edgegw']
        self.username = cloud_params['username']
        self.passwd = cloud_params['passwd']

        self.region_name = cloud_params['region_name']
        self.availabilityzone = cloud_params['availabilityzone']
        self.azname = cloud_params['azname']

        self.cascaded_eip = install_info["cascaded"]["public_ip_api_reverse"]
        self.vpn_eip = install_info["vpn"]["public_ip_vpn"],
        self.cloud_proxy = proxy_info
        self.driver_type = cloud_params['driver_type']
        self.access = cloud_params['access']

    def get_exist_cloud(self, cloud_id, vcloud_url, vcloud_org, vcloud_vdc, vcloud_edgegw, username, passwd,
                 region_name, availabilityzone, azname,
                 cascaded_domain, cascaded_eip, vpn_eip, cloud_proxy=None,
                 driver_type="agentleass", access=True, with_ceph=True):
        self.cloud_id = cloud_id
        self.vcloud_url = vcloud_url
        self.vcloud_org = vcloud_org
        self.vcloud_vdc = vcloud_vdc
        self.vcloud_edgegw = vcloud_edgegw
        self.username = username
        self.passwd = passwd
        self.region_name = region_name
        self.availabilityzone = availabilityzone
        self.azname = azname
        self.cascaded_domain = cascaded_domain
        self.cascaded_eip = cascaded_eip
        self.vpn_eip = vpn_eip
        self.cloud_proxy = cloud_proxy
        self.driver_type = driver_type
        self.access = access
        self.with_ceph = with_ceph

    def get_vpn_conn_name(self):
        vpn_conn_name = {"api_conn_name": self.cloud_id + '-api',
                         "tunnel_conn_name": self.cloud_id + '-tunnel'}
        return vpn_conn_name

def _read_vcloud_access_cloud_info():
    vcloud_hybrid_cloud = {}
    if not os.path.exists(_hws_access_cloud_data_file):
        LOG.error("read %s : No such file." % _hws_access_cloud_data_file)
    else:
        with open(_hws_access_cloud_data_file, 'r+') as fd:
            try:
                vcloud_hybrid_cloud = json.loads(fd.read())
            except:
                pass
    return vcloud_hybrid_cloud


def _write_vcloud_access_cloud_info(vcloud_hybrid_clouds):
    with open(_hws_access_cloud_data_file, 'w+') as fd:
        fd.write(json.dumps(vcloud_hybrid_clouds, indent=4))


def get_vcloud_access_cloud(cloud_id):
    _hws_access_cloud_data_file_lock.acquire()
    try:
        cloud_dict = _read_vcloud_access_cloud_info()
    except Exception as e:
        cloud_dict = {}
        LOG.error("get vcloud access cloud info error, cloud_id: %s, error: %s"
                     % (cloud_id, e.message))
    finally:
        _hws_access_cloud_data_file_lock.release()

    if cloud_id in cloud_dict.keys():
        return cloud_dict[cloud_id]
    else:
        return None


def delete_vcloud_access_cloud(cloud_id):
    _hws_access_cloud_data_file_lock.acquire()
    try:
        cloud_dict = _read_vcloud_access_cloud_info()
        if cloud_id in cloud_dict.keys():
            cloud_dict.pop(cloud_id)
        _write_vcloud_access_cloud_info(cloud_dict)
    except Exception as e:
        LOG.error("delete vcloud access cloud error, cloud_id: %s, error: %s"
                     % (cloud_id, e.message))
    finally:
        _hws_access_cloud_data_file_lock.release()


def _get_unit_info(cloud_id, unit_key):
    cloud_info = get_vcloud_access_cloud(cloud_id)
    if not cloud_info:
        return None

    if unit_key in cloud_info.keys():
        return cloud_info[unit_key]
    else:
        return None


def _write_unit_info(cloud_id, unit_key, unit_value):
    _hws_access_cloud_data_file_lock.acquire()
    try:
        cloud_dict = _read_vcloud_access_cloud_info()
        if cloud_id in cloud_dict.keys():
            cloud_dict[cloud_id][unit_key] = unit_value
        else:
            cloud_dict[cloud_id] = {unit_key: unit_value}
        _write_vcloud_access_cloud_info(cloud_dict)
    except Exception as e:
        LOG.error("write access cloud unit info error, "
                     "cloud_id: %s, unit_key: %s, unit_value: %s, error: %s"
                     % (cloud_id, unit_key, unit_value, e.message))
    finally:
        _hws_access_cloud_data_file_lock.release()

def get_cascaded(cloud_id):
    return _get_unit_info(cloud_id, "cascaded")


def get_vpn(cloud_id):
    return _get_unit_info(cloud_id, "vpn")


def get_ext_net_eips(cloud_id):
    return _get_unit_info(cloud_id, "ext_net_eips")

#TODO(lrx):modify vpc to vcloud network
def write_vdc_network(cloud_id, api_gw ,
                                api_subnet_cidr ,
                                tunnel_gw ,
                                tunnel_subnet_cidr):
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


