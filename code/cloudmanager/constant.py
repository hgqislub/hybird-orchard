# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import os


class PublicConstant(object):
    SCRIPTS_DIR = os.path.join("/home/hybrid_cloud",
                               "scripts", "public")
    ADD_HOST_ADDRESS_SCRIPT = "add_host_address.sh"
    MODIFY_DNS_SERVER_ADDRESS = "modify_dns_server_address.sh"


class VpnConstant(object):
    VPN_ROOT = "root"
    VPN_ROOT_PWD = "Galax0088"
    AWS_VPN_ROOT = "root"
    AWS_VPN_ROOT_PWD = "Galax0088"
    VCLOUD_VPN_ROOT = "root"
    VCLOUD_VPN_ROOT_PWD = "Galax0088"
    REMOTE_SCRIPTS_DIR = "/root/ipsec_config/"
    LIST_TUNNEL_SCRIPT = "list_tunnel.sh"
    ADD_TUNNEL_SCRIPT = "add_tunnel_ex.sh"
    REMOVE_TUNNEL_SCRIPT = "remove_tunnel.sh"
    REMOTE_ROUTE_SCRIPTS_DIR = "/home/hybrid_cloud/scripts/vpn/"
    ADD_VPN_ROUTE_SCRIPT = "add_vpn_route.sh"
    MODIFY_CASCADED_API_SCRIPT = "modify_cascaded_api.py"

class Cascaded(object):
    ROOT = "root"
    ROOT_PWD = "cnp200@HW"
    REMOTE_SCRIPTS_DIR = "/root/cloud_manager/cascaded/"
    REMOTE_VCLOUD_SCRIPTS_DIR = "/home/hybrid_cloud/scripts/cascaded/"
    REMOTE_HWS_SCRIPTS_DIR = "/home/hybrid_cloud/scripts/cascaded/"
    CONFIG_VCLOUD_SCRIPT = "config_vcloud.sh"
    MODIFY_PROXY_SCRIPT = "modify_proxy.sh"
    MODIFY_CASCADED_SCRIPT = "modify_cascaded_domain.sh"
    MODIFY_CASCADED_SCRIPT_PY = "cascaded_handler.py"
    CASCADED_ADD_ROUTE_SCRIPT = "cascaded_add_route.sh"
    ADD_ROUTE_SCRIPT = "add_route.sh"
    ADD_API_ROUTE_SCRIPT = "cascaded_add_api_route.sh"
    CREATE_ENV = "create_env.sh"
    CONFIG_CINDER_SCRIPT = "config_storage.sh"
    CONFIG_CINDER_BACKUP_SCRIPT = "ceph_patch/backup_az.py"
    UPDATE_NETWORK_VLAN_SCRIPT = "update_network_vlan.sh"
    UPDATE_L3_AGENT_SCRIPT = "update_neutron_l3_agent.sh"


class Cascading(object):
    ROOT = "root"
    ROOT_PWD = "Huawei@CLOUD8!"
    REMOTE_SCRIPTS_DIR = "/home/hybrid_cloud/scripts/cascading/"
    CHECK_PROXY_SCRIPT = "check_free_proxy.sh"
    ADD_VPN_ROUTE_SCRIPT = "add_vpn_route.sh"
    ADD_VPN_ROUTE_TUNNEL_SCRIPT = "add_vpn_tunnel_route.sh"
    KEYSTONE_ENDPOINT_SCRIPT = "create_keystone_endpoint.sh"
    ENABLE_OPENSTACK_SERVICE = "enable_openstack_service.sh"
    UPDATE_PROXY_PARAMS = "modify_proxy_params.sh"
    ENV_FILE = "/home/hybrid_cloud/conf/env.conf"

class AfterRebootConstant(object):
    REMOTE_SCRIPTS_DIR = "/home/hybrid_cloud/scripts/after_reboot/"
    REMOTE_ROUTE_SCRIPTS_DIR = "/home/hybrid_cloud/scripts/after_reboot/add_vpn_route"
    ADD_ROUTE_SCRIPT = "add_vpn_route.sh"


class PatchesConstant(object):
    REMOTE_SCRIPTS_DIR = "/home/hybrid_cloud/scripts/patches/"
    PATCH_LUNCH_DIR = "/home/hybrid_cloud/scripts/patches/patches_tool"
    CONFIG_PATCHES_SCRIPT = "config_patches_tool_config.sh"
    CONFIG_AWS_SCRIPT = "config_aws.sh"
    CONFIG_ROUTE_SCRIPT = "config_add_route.sh"
    REMOTE_HWS_SCRIPTS_DIR = "/home/hybrid_cloud/scripts/patches/patches_tool/hws_patch"
    CONFIG_HWS_SCRIPT = "config_hws.sh"
    START_HWS_GATEWAY_SCRIPT = "hws_gateway.sh"


class RemoveConstant(object):
    REMOTE_SCRIPTS_DIR = "/home/hybrid_cloud/scripts/remove/"
    REMOVE_KEYSTONE_SCRIPT = "remove_keystone_endpoint.sh"
    REMOVE_PROXY_SCRIPT = "remove_proxy_host.sh"
    REMOVE_AGGREGATE_SCRIPT = "remove_aggregate.sh"
    REMOVE_CINDER_SERVICE_SCRIPT = "remove_cinder_service.sh"
    REMOVE_NEUTRON_AGENT_SCRIPT = "remove_neutron_agent.sh"
    REMOVE_ROUTE_SCRIPT = "remove_route.sh"


class CephConstant(object):
    USER = "ceph"
    PWD = "ceph@huawei"
    CEPH_INSTALL_SCRIPT = "/home/ceph/config-sh/install.sh"


class Proxy(object):
    USER = "root"
    PWD = "Huawei@CLOUD8!"
    LOCAL_NEUTRON_PROXY_DIR = "/home/hybrid_cloud/code/proxy/neutron_proxy"
    REMOTE_NEUTRON_PROXY_DIR = "/usr/lib64/python/site-packages/neutron/agent"
    L3_PROXY_CODE = "l3_proxy.py"
    
    LOCAL_CINDER_PROXY_DIR = "/home/hybrid_cloud/code/proxy/cinder_proxy"
    REMOTE_CINDER_PROXY_DIR = "/usr/lib64/python2.6/site-packages/cinder/proxy"
    CINDER_PROXY_CODE = "cinder_proxy.py"
    
class FsCascaded(object):
    LOCAL_GLANCE_DIR = "/home/hybrid_cloud/code/cascaded/glance"
    REMOTE_GLANCE_DIR = "/usr/lib64/python2.6/site-packages/glance/common"
    GLANCE_CODE = "config.py"
    
    LOCAL_CINDER_DIR = "/home/hybrid_cloud/code/cascaded/cinder"
    REMOTE_CINDER_DIR = "/usr/lib64/python2.6/site-packages/cinder/volume"
    CINDER_VOLUME_API_CODE = "api.py"
    
    
    REMOTE_SCRIPTS_DIR = "/home/hybrid_cloud/scripts/cascaded"
    ADD_ROUTE_SCRIPT = "add_vpn_route.sh"

class FusionsphereConstant(object):
    ROOT = "root"
    ROOT_PWD = "Huawei@CLOUD8!"


class VcloudConstant(object):
    ROOT = "root"
    ROOT_PWD = "Huawei@CLOUD8!"

class HwsConstant(object):
    ROOT = "root"
    ROOT_PWD = "Huawei@CLOUD8!"
    CLOUD_INFO_FILE = "/home/hybrid_cloud/data/hws/hws_access_cloud.data"
    INSTALL_INFO_FILE = "/home/hybrid_cloud/data/hws/hws_access_cloud_install.data"

class AwsConstant(object):
    ROOT = "root"
    ROOT_PWD = "cnp200@HW"

