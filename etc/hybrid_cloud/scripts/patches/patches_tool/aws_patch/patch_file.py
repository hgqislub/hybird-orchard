#!/usr/bin/env python
# -*-coding:utf-8-*-

__author__ = 'luqitao'

import json
import log as LOG
import os
import socket
import sys
import time

from oslo.config import cfg

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.extend([CURRENT_PATH + "/../../", "/usr/bin/"])

import utils
from install_tool import cps_server
from patches_tool.services import RefServices, RefCPSServiceExtent, \
    RefCPSService, RefFsSystemUtils
from patches_tool import config

PROVIDER_API_NETWORK = 'provider_api_network_id'
PROVIDER_TUNNEL_NETWORK = 'provider_tunnel_network_id'

provider_opts = [
    cfg.StrOpt('conversion_dir',
               default='/opt/HUAWEI/image',
               help='conversion_dir.'),
    cfg.StrOpt('access_key_id',
               default='',
               help='access_key_id from aws user config.'),
    cfg.StrOpt('secret_key',
               default='',
               help='secret_key from aws user config'),
    cfg.StrOpt('region',
               default='ap-southeast-1',
               help='region name from aws user config'),
    cfg.StrOpt('availability_zone',
               default='ap-southeast-1a',
               help='availability_zone'),
    cfg.StrOpt('base_linux_image',
               default='ami-68d8e93a',
               help='base_linux_image'),
    cfg.StrOpt('storage_tmp_dir',
               default='hybridbucket',
               help='storage_tmp_dir'),
    cfg.StrOpt('cascaded_node_id',
               default='i-test',
               help='cascaded_node_id'),
    cfg.StrOpt('subnet_data',
               default='subnet-bf28f8c8',
               help='subnet_data'),
    cfg.StrOpt('subnet_api',
               default='subnet-3d28f84a',
               help='subnet_api'),
    cfg.StrOpt('flavor_map',
               default='m1.tiny:t2.micro, m1.small:t2.micro, '
                       'm1.medium:t2.micro3, m1.large:t2.micro, '
                       'm1.xlarge:t2.micro',
               help='map nova flavor name to vcloud vm specification id'),
    cfg.StrOpt('cgw_host_ip',
               default='52.74.155.248',
               help='cgw_host_ip'),
    cfg.StrOpt('cgw_host_id',
               default='i-c124700d',
               help='cgw_host_id'),
    cfg.StrOpt('cgw_user_name',
               default='ec2-user',
               help='cgw_user_name'),
    cfg.StrOpt('cgw_certificate',
               default='/home/cgw.pem',
               help='cgw_certificate'),
    cfg.StrOpt('rabbit_password_public',
               default='',
               help='rabbit_password_public'),
    cfg.StrOpt('rabbit_host_ip_public',
               default='162.3.120.64',
               help='rabbit_host_ip_public'),
    cfg.StrOpt('vpn_route_gateway',
               default='162.3.0.0/16:172.29.0.1,172.28.48.0/20:172.29.1.1',
               help='vpn_route_gateway'),
    cfg.StrOpt('driver_type', default='agentless')]

vtepdriver = [
    cfg.StrOpt('provider_api_network_name',
               default='subnet-3d28f84a',
               help='a network name which is used for api tunnel on aws.'
                    'host.'),
    cfg.StrOpt('provider_tunnel_network_name',
               default='subnet-bf28f8c8',
               help='a network name which is used for data tunnel on aws.')]

hypernode_api = [
    cfg.StrOpt('rabbit_userid', default='rabbit'),
    cfg.StrOpt('rabbit_password_public', default='FusionSphere123'),
    cfg.StrOpt('cidr_vms', default='172.29.124.0/24'),
    cfg.StrOpt('cidr_hns', default='172.29.252.0/24'),
    cfg.StrOpt('subnet_tunnel_bearing', default=''),
    cfg.StrOpt('subnet_internal_base', default=''),
    cfg.StrOpt('hn_image_id', default='ami-0ec8c913'),
    cfg.StrOpt('hn_flavor', default='c4.large'),
    cfg.StrOpt('hypernode_name', default='06a87ef2c5f3'),
    cfg.StrOpt('vpc_id', default='vpc-78ae0011'),
    cfg.StrOpt('my_ip', default='172.29.124.12'),
    cfg.StrOpt('ip_vpngw', default='172.29.0.1')
]

keystone_authtoken = [
    cfg.StrOpt('tenant_name', default='admin'),
    cfg.StrOpt('user_name', default='cloud_admin'),
    cfg.StrOpt('keystone_auth_url',
               default='https://identity.cloud.hybrid.huawei.com:443/identity-admin/v2.0')
]

CONF = cfg.CONF
group_provider_opts = cfg.OptGroup(name='provider_opts', title='provider opts')
group_vtepdriver = cfg.OptGroup(name='vtepdriver', title='vtep')
CONF.register_group(group_provider_opts)
CONF.register_group(group_vtepdriver)
CONF.register_opts(provider_opts, group_provider_opts)
CONF.register_opts(vtepdriver, group_vtepdriver)

group_hypernode_api = cfg.OptGroup(name='hypernode_api', title='hypernode_api')
CONF.register_group(group_hypernode_api)
CONF.register_opts(hypernode_api, group_hypernode_api)

group_keystone_authtoken = cfg.OptGroup(name='keystone_authtoken',
                                        title='keystone_authtoken')
CONF.register_group(group_keystone_authtoken)
CONF.register_opts(keystone_authtoken, group_keystone_authtoken)

aws_config_ini = os.path.join(CURRENT_PATH, 'aws_config.ini')
CONF(['--config-file=%s' % aws_config_ini])


def restart_component(service_name, template_name):
    """Stop an component, then start it."""

    ret = RefCPSServiceExtent.host_template_instance_operate(service_name,
                                                             template_name,
                                                             'stop')
    if not ret:
        LOG.error(
            "cps template_instance_action stop for %s failed." % template_name)
        return ret
    ret = RefCPSServiceExtent.host_template_instance_operate(service_name,
                                                             template_name,
                                                             'start')
    if not ret:
        LOG.error(
            "cps template_instance_action start for %s failed." % template_name)
        return ret


def config_cascaded_az():
    """Update parameter for neutron-server and cinder-volume, then restart them."""

    params = {
        'mechanism_drivers':
            'openvswitch,l2populationcascaded,'
            'evs,sriovnicswitch,netmapnicswitch'}
    ret = cps_server.update_template_params('neutron', 'neutron-server', params)
    if not ret:
        LOG.error("cps update_template_params for neutron-server failed.")
        return ret

    params = {
        'volume_driver': 'cinder.volume.drivers.ec2.driver.AwsEc2VolumeDriver'}
    ret = cps_server.update_template_params('cinder', 'cinder-volume', params)
    if not ret:
        LOG.error("cps update_template_params for cinder-volume failed.")
        return ret

    cps_server.cps_commit()

    restart_component('neutron', 'neutron-openvswitch-agent')
    restart_component('cinder', 'cinder-volume')
    restart_component('nova', 'nova-compute')


def replace_config(conf_file_path, src_key, new_value):
    """Update the config file by a given dict."""

    with open(conf_file_path, "a+") as fp:
        content = json.load(fp)

        content[src_key].update(new_value)
        fp.truncate(0)
        fp.write(json.dumps(content, indent=4))


def replace_cinder_volume_config(conf_file_path):
    """ Get config from aws_config.ini"""

    with open(conf_file_path, "a+") as fp:
        content = json.load(fp)

        content['cinder.conf']['keystone_authtoken'][
            'tenant_name'] = CONF.keystone_authtoken.tenant_name
        content['cinder.conf']['keystone_authtoken'][
            'user_name'] = CONF.keystone_authtoken.user_name
        content['cinder.conf']['keystone_authtoken'][
            'keystone_auth_url'] = CONF.keystone_authtoken.keystone_auth_url

        fp.truncate(0)
        fp.write(json.dumps(content, indent=4))


def replace_all_config():
    aws_conf = construct_aws_conf()

    for i in range(50):
        try:
            api_net_id, tunnel_net_id = get_api_tunnel_netid()
            break
        except Exception as e:
            LOG.error("get api tunnel netid error, try again.")
            time.sleep(6)

    aws_conf['vtepdriver'][PROVIDER_API_NETWORK] = api_net_id
    aws_conf['vtepdriver'][PROVIDER_TUNNEL_NETWORK] = tunnel_net_id

    cur_path = os.path.split(os.path.realpath(__file__))[0]
    nova_compute_path = os.path.join(cur_path, "code", "etc", "nova", "others",
                                     "cfg_template", "nova-compute.json")
    replace_config(nova_compute_path, "nova.conf", aws_conf)

    # Get config from aws_config.ini
    cinder_volume_path = os.path.join(cur_path, "code", "etc", "cinder",
                                      "others", "cfg_template",
                                      "cinder-volume.json")
    replace_cinder_volume_config(cinder_volume_path)


def patch_hybridcloud_files():
    """Execute a shell script, do this things:
    1. replace python code
    2. update configuration files
    3. install some dependence packages
    4. restart component proc
    """

    utils.execute(['dos2unix', os.path.join(CURRENT_PATH, 'install.sh')])
    utils.execute(['sh', os.path.join(CURRENT_PATH, 'install.sh')])


def construct_aws_conf():
    """Build a json format config by ini file"""
    provider_opts_data = {}
    for o in CONF.provider_opts:
        provider_opts_data[o] = str(eval("CONF.provider_opts.%s" % o))

    vtepdriver_data = {}
    for o in CONF.vtepdriver:
        vtepdriver_data[o] = str(eval("CONF.vtepdriver.%s" % o))

    hypernode_api_data = {}
    for o in CONF.hypernode_api:
        hypernode_api_data[o] = str(eval("CONF.hypernode_api.%s" % o))

    return {"provider_opts": provider_opts_data, "vtepdriver": vtepdriver_data,
            "hypernode_api": hypernode_api_data}


def get_networkid_by_name(networks_data, name):
    if isinstance(networks_data, dict):
        if networks_data.has_key('networks'):
            for d in networks_data['networks']:
                if d['name'] == name:
                    return d['id']


def get_api_tunnel_netid():
    """Get api and tunnel network id from neutron api, create if it doesn't exist."""
    rs = RefServices(region_name=os.environ['OS_REGION_NAME'])
    networks_data = rs.neutron.list_networks()

    api_netid = get_networkid_by_name(networks_data, PROVIDER_API_NETWORK)
    tunnel_netid = get_networkid_by_name(networks_data, PROVIDER_TUNNEL_NETWORK)

    body = {"network": {"provider:network_type": "vlan",
                        "provider:physical_network": "physnet1"}}
    if api_netid is None:
        body['network']['name'] = PROVIDER_API_NETWORK
        # TODO deal with create network failed.
        api_netdata = rs.neutron.create_network(body)
        api_netid = api_netdata['network']['id']
    if tunnel_netid is None:
        body['network']['name'] = PROVIDER_TUNNEL_NETWORK
        # TODO deal with create network failed.
        tunnel_netdata = rs.neutron.create_network(body)
        tunnel_netid = tunnel_netdata['network']['id']
    return api_netid, tunnel_netid


def create_aggregate_in_cascaded_node():
    """
    nova aggregate-create az31.singapore--aws az31.singapore--aws
    nova host-list
    nova aggregate-add-host az31.singapore--aws 42114FD9-D446-9248-3A05-23CF474E3C68

    :return:
    """
    host_id = socket.gethostname()
    region = RefCPSService.get_local_domain()
    os_region_name = '.'.join([RefFsSystemUtils.get_az_by_domain(region),
                               RefFsSystemUtils.get_dc_by_domain(region)])
    ref_service = RefServices()
    if not ref_service.nova_aggregate_exist(os_region_name, os_region_name):
        create_result = ref_service.nova_aggregate_create(os_region_name,
                                                          os_region_name)
        if create_result is not None:
            ref_service.nova_aggregate_add_host(os_region_name, host_id)


def update_cinder_volume_other_storage_cfg():
    service = "cinder"
    template = "cinder-volume"
    cascaded_domain = cps_server.get_local_domain()
    cascaded_region = _get_region_form_domain(cascaded_domain)

    rbd = {'iscsi_server_ip': '172.29.253.11',
           'rbd_store_chunk_size': '4',
           'rbd_ceph_conf': '/etc/ceph/ceph.conf',
           'volume_backend_name': 'HYBRID:%s:%s'
                                  % (cascaded_region, cascaded_region),
           'iscsi_server_pem': '/home/ceph-keypair.pem',
           'volume_driver':
               'cinder.volume.drivers.cephiscsi.cephiscsi.CephIscsiDriver',
           'rbd_user': 'cinder',
           'rados_connect_timeout': '-1',
           'rbd_pool': 'volumes',
           'rbd_flatten_volume_from_snapshot': 'false',
           'rbd_max_clone_depth': '5',
           'iscsi_server_user': 'ceph'}

    ec2 = {'storage_tmp_dir': CONF.provider_opts.storage_tmp_dir,
           'availability_zone': CONF.provider_opts.availability_zone,
           'cgw_host_ip': CONF.provider_opts.cgw_host_ip,
           'cgw_certificate': CONF.provider_opts.cgw_certificate,
           'volume_backend_name': 'AMAZONEC2',
           'region': CONF.provider_opts.region,
           'provider_image_conversion_dir': CONF.provider_opts.conversion_dir,
           'volume_driver':
               'cinder.volume.drivers.ec2.driver.AwsEc2VolumeDriver',
           'access_key_id': CONF.provider_opts.access_key_id,
           'secret_key': CONF.provider_opts.secret_key,
           'cgw_username': CONF.provider_opts.cgw_user_name,
           'cgw_host_id': CONF.provider_opts.cgw_host_id}

    other_storage_cfg_temp = {"rbd": rbd,
                              "ec2": ec2}

    other_storage_cfg = {0: other_storage_cfg_temp}
    updated_params = {
        "other_storage_cfg": other_storage_cfg
    }
    return cps_server.update_template_params(service, template, updated_params)


def _get_region_form_domain(cascaded_domain):
    arr = cascaded_domain.split(".")
    cascaded_local_az = arr[0]
    cascaded_local_dc = arr[1]
    return ".".join([cascaded_local_az, cascaded_local_dc])


if __name__ == '__main__':
    LOG.init('patches_tool_config')
    LOG.info('START to patch for aws...')
    config.export_region()

    try:
        replace_all_config()
    except Exception as e:
        LOG.error('Exception when replace_all_config, Exception: %s'
                  % e.message)

    LOG.info('Start to patch for hybrid-cloud files')
    try:
        patch_hybridcloud_files()
    except Exception as e:
        LOG.error('Exception when patch for hybrid-cloud files, Exception: %s'
                  % e.message)

    LOG.info("update cinder-volume params")
    try:
        update_cinder_volume_other_storage_cfg()
    except Exception as e:
        LOG.error("update cinder-volume params error, error: %s"
                  % e.message)

    try:
        LOG.info('Start to create ag in aws node.')
        create_aggregate_in_cascaded_node()
        LOG.info('Start to config cascaded az.')
        config_cascaded_az()
    except Exception as e:
        LOG.error('Exception when create cascaded az, Exception: %s'
                  % e.message)

    LOG.info('SUCCESS to patch for aws.')
