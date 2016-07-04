# -*- coding:utf-8 -*-

import sys
sys.path.append("..")


import os
from heat.openstack.common import log as logging
import json
import vcloud_proxy_data_handler
from pyvcloud import vcloudair

LOG=logging.getLogger(__name__)

_vcloud_proxy_install_conf = os.path.join("/home/hybrid_cloud/conf",
                                       "vcloud_proxy_install.conf")

_vcloud_vdc_info = os.path.join("/home/hybrid_cloud/conf",
                             "vcloud_vdc.conf")

LOG = logging.getLogger(__name__)


def _read_install_conf():
    if not os.path.exists(_vcloud_proxy_install_conf):
        LOG.error("read %s : No such file." % _vcloud_proxy_install_conf)
        return None
    with open(_vcloud_proxy_install_conf, 'r+') as fd:
        tmp = fd.read()
        return json.loads(tmp)


def _write_install_conf():
    #TODO(lrx):change the install_conf params
    install_conf = {"proxy_image": "OpenStack-B111T-v0.994",
                    "proxy_vm_type": "c3.xlarge"}
    with open(_vcloud_proxy_install_conf, 'w+') as fd:
        fd.write(json.dumps(install_conf, indent=4))
        return install_conf


def _read_vdc_info():
    if not os.path.exists(_vcloud_vdc_info):
        LOG.error("read %s : No such file." % _vcloud_vdc_info)
        return None
    with open(_vcloud_vdc_info, 'r+') as fd:
        tmp = fd.read()
        return json.loads(tmp)


def install_vcloud_proxy():
    #TODO(lrx):modify the proxy params
    vdc_info = _read_vdc_info()
    vcloud_url = vdc_info['vcloud_url']
    vcloud_org = vdc_info['vcloud_org']
    vcloud_vdc = vdc_info['vcloud_vdc']
    username = vdc_info['username']
    passwd = vdc_info['passwd']
    az = vdc_info['az']
    # tunnel_subnet_id = vpc_info["tunnel_subnet_id"]
    # base_subnet_id = vpc_info["base_subnet_id"]

    installer = vcloudair.VCA(host=vcloud_url, username=username, service_type='vcd', version='5.5', verify=True)

    # tunnel_en = aws_util.AWSInterface(tunnel_subnet_id)
    # base_en = aws_util.AWSInterface(base_subnet_id)

    proxy_install_conf = _read_install_conf()

    installer.login(password=passwd, org=vcloud_org)

    proxy_vm = installer.create_vapp(vcloud_vdc,vapp_name=az,
                                     template_name=proxy_install_conf["proxy_image"],
                                     catalog_name='share_dir',
                                     poweron='true'
                                     )

    vcloud_proxy_data_handler.add_new_proxy(proxy_vm.id)


def remove_all_proxys():
    #TODO(lrx):get vapp list
    vdc_info = _read_vdc_info()
    vcloud_url = vdc_info['vcloud_url']
    vcloud_org = vdc_info['vcloud_org']
    vcloud_vdc = vdc_info['vcloud_vdc']
    username = vdc_info['username']
    passwd = vdc_info['passwd']
    az = vdc_info['az']
    installer = vcloudair.VCA(host=vcloud_url, username=username, service_type='vcd', version='5.5', verify=True)
    installer.login(password=passwd, org=vcloud_org)


    #TODO(lrx):change the vapp name 
    proxy_vm_id = installer.get_vapp(vdc=vcloud_vdc, vapp_name='OPenStack-AZ11')
    proxy_vm_ids = vcloud_proxy_data_handler.get_vcloud_proxy_list()
    for proxy_vm_id in proxy_vm_ids:
        installer.terminate_instance(proxy_vm_id)


if __name__ == '__main__':
    LOG.init("ProxyInstall", output=True)
    # install_aws_proxy()

    remove_all_proxys()
