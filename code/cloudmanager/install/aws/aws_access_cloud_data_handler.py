import threading
import os
import json
from heat.openstack.common import log as logger
_aws_access_cloud_data_file = os.path.join("/home/hybrid_cloud/data",
                                           "aws_access_cloud_install.data")
_aws_access_cloud_data_file_lock = threading.Lock()


def _read_aws_access_cloud_info():
    aws_hybrid_cloud = {}
    if not os.path.exists(_aws_access_cloud_data_file):
        logger.error("read %s : No such file." % _aws_access_cloud_data_file)
    else:
        with open(_aws_access_cloud_data_file, 'r+') as fd:
            try:
                aws_hybrid_cloud = json.loads(fd.read())
            except:
                pass
    return aws_hybrid_cloud


def _write_aws_access_cloud_info(aws_hybrid_clouds):
    with open(_aws_access_cloud_data_file, 'w+') as fd:
        fd.write(json.dumps(aws_hybrid_clouds, indent=4))


def get_aws_access_cloud(cloud_id):
    _aws_access_cloud_data_file_lock.acquire()
    try:
        cloud_dict = _read_aws_access_cloud_info()
    except Exception as e:
        cloud_dict = {}
        logger.error("get aws access cloud info error, cloud_id: %s, error: %s"
                     % (cloud_id, e.message))
    finally:
        _aws_access_cloud_data_file_lock.release()

    if cloud_id in cloud_dict.keys():
        return cloud_dict[cloud_id]
    else:
        return None


def delete_aws_access_cloud(cloud_id):
    _aws_access_cloud_data_file_lock.acquire()
    try:
        cloud_dict = _read_aws_access_cloud_info()
        if cloud_id in cloud_dict.keys():
            cloud_dict.pop(cloud_id)
        _write_aws_access_cloud_info(cloud_dict)
    except Exception as e:
        logger.error("delete aws access cloud error, cloud_id: %s, error: %s"
                     % (cloud_id, e.message))
    finally:
        _aws_access_cloud_data_file_lock.release()


def _get_unit_info(cloud_id, unit_key):
    cloud_info = get_aws_access_cloud(cloud_id)
    if not cloud_info:
        return None

    if unit_key in cloud_info.keys():
        return cloud_info[unit_key]
    else:
        return None


def _write_unit_info(cloud_id, unit_key, unit_value):
    _aws_access_cloud_data_file_lock.acquire()
    try:
        cloud_dict = _read_aws_access_cloud_info()
        if cloud_id in cloud_dict.keys():
            cloud_dict[cloud_id][unit_key] = unit_value
        else:
            cloud_dict[cloud_id] = {unit_key: unit_value}
        _write_aws_access_cloud_info(cloud_dict)
    except Exception as e:
        logger.error("write access cloud unit info error, "
                     "cloud_id: %s, unit_key: %s, unit_value: %s, error: %s"
                     % (cloud_id, unit_key, unit_value, e.message))
    finally:
        _aws_access_cloud_data_file_lock.release()


def get_vpc(cloud_id):
    return _get_unit_info(cloud_id, "vpc")


def get_cascaded(cloud_id):
    return _get_unit_info(cloud_id, "cascaded")


def get_vpn(cloud_id):
    return _get_unit_info(cloud_id, "vpn")


def get_v2v_gateway(cloud_id):
    return _get_unit_info(cloud_id, "v2v_gateway")


def get_hynode(cloud_id):
    return _get_unit_info(cloud_id, "hynode")


def get_ceph(cloud_id):
    return _get_unit_info(cloud_id, "ceph_cluster")


def get_ext_net_eips(cloud_id):
    return _get_unit_info(cloud_id, "ext_net_eips")


def write_vpc(cloud_id, vpc_id,
              debug_subnet_cidr, debug_subnet_id,
              base_subnet_cidr, base_subnet_id,
              api_subnet_id_cidr, api_subnet_id,
              tunnel_subnet_cidr, tunnel_subnet_id,
              ceph_subnet_cidr, ceph_subnet_id,
              gateway_id, rtb_id):
    vpn_info = {"vpc_id": vpc_id,
                "debug_subnet_cidr": debug_subnet_cidr,
                "debug_subnet_id": debug_subnet_id,
                "base_subnet_cidr": base_subnet_cidr,
                "base_subnet_id": base_subnet_id,
                "api_subnet_cidr": api_subnet_id_cidr,
                "api_subnet_id": api_subnet_id,
                "tunnel_subnet_cidr": tunnel_subnet_cidr,
                "tunnel_subnet_id": tunnel_subnet_id,
                "ceph_subnet_cidr": ceph_subnet_cidr,
                "ceph_subnet_id": ceph_subnet_id,
                "gateway_id": gateway_id,
                "rtb_id": rtb_id}
    _write_unit_info(cloud_id, "vpc", vpn_info)


def write_cascaded(cloud_id,
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

    _write_unit_info(cloud_id, "cascaded", cascaded_info)


def write_vpn(cloud_id,
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

    _write_unit_info(cloud_id, "vpn", vpn_info)


def write_v2v_gateway(cloud_id, v2v_vm_id, v2v_ip):
    v2v_info = {"vm_id": v2v_vm_id,
                "ip": v2v_ip}
    _write_unit_info(cloud_id, "v2v_gateway", v2v_info)


def write_hynode(cloud_id, hynode_image_id):
    hynode_info = {"image_id": hynode_image_id}
    _write_unit_info(cloud_id, "hynode", hynode_info)


def write_ceph_cluster(cloud_id,
                       ceph_deploy_vm_id, ceph_deploy_ip,
                       ceph_node1_vm_id, ceph_node1_ip,
                       ceph_node2_vm_id, ceph_node2_ip,
                       ceph_node3_vm_id, ceph_node3_ip):
    ceph_cluster_info = {"deploy_vm_id": ceph_deploy_vm_id,
                         "deploy_ip": ceph_deploy_ip,
                         "node1_vm_id": ceph_node1_vm_id,
                         "node1_ip": ceph_node1_ip,
                         "node2_vm_id": ceph_node2_vm_id,
                         "node2_ip": ceph_node2_ip,
                         "node3_vm_id": ceph_node3_vm_id,
                         "node3_ip": ceph_node3_ip}

    _write_unit_info(cloud_id,
                     "ceph_cluster", ceph_cluster_info)


def write_ext_net_eip(cloud_id, ext_net_eips):
    _write_unit_info(cloud_id, "ext_net_eips", ext_net_eips)
