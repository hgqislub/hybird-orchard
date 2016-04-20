# -*- coding:utf-8 -*-

__author__ = 'q00222219@huawei'

import os
import log as logger
import json
import aws_util
import aws_proxy_data_handler

_aws_proxy_install_conf = os.path.join("/home/hybrid_cloud/conf",
                                       "aws_proxy_install.conf")

_aws_vpc_info = os.path.join("/home/hybrid_cloud/conf",
                             "aws_vpc.conf")


def _read_install_conf():
    if not os.path.exists(_aws_proxy_install_conf):
        logger.error("read %s : No such file." % _aws_proxy_install_conf)
        return None
    with open(_aws_proxy_install_conf, 'r+') as fd:
        tmp = fd.read()
        return json.loads(tmp)


def _write_install_conf():
    install_conf = {"proxy_image": "OpenStack-B111T-v0.994",
                    "proxy_vm_type": "c3.xlarge"}
    with open(_aws_proxy_install_conf, 'w+') as fd:
        fd.write(json.dumps(install_conf, indent=4))
        return install_conf


def _read_vpc_info():
    if not os.path.exists(_aws_vpc_info):
        logger.error("read %s : No such file." % _aws_vpc_info)
        return None
    with open(_aws_vpc_info, 'r+') as fd:
        tmp = fd.read()
        return json.loads(tmp)


def install_aws_proxy():
    vpc_info = _read_vpc_info()
    access_key = vpc_info["access_key"]
    secret_key = vpc_info["secret_key"]
    region = vpc_info["region"]
    az = vpc_info["az"]
    tunnel_subnet_id = vpc_info["tunnel_subnet_id"]
    base_subnet_id = vpc_info["base_subnet_id"]

    installer = aws_util.AWSInstaller(access_key, secret_key, region, az)

    tunnel_en = aws_util.AWSInterface(tunnel_subnet_id)
    base_en = aws_util.AWSInterface(base_subnet_id)

    proxy_install_conf = _read_install_conf()
    proxy_vm = installer.create_vm(proxy_install_conf["proxy_image"],
                                   proxy_install_conf["proxy_vm_type"],
                                   tunnel_en, base_en)
    aws_proxy_data_handler.add_new_proxy(proxy_vm.id)


def remove_all_proxys():
    vpc_info = _read_vpc_info()
    access_key = vpc_info["access_key"]
    secret_key = vpc_info["secret_key"]
    region = vpc_info["region"]
    az = vpc_info["az"]
    installer = aws_util.AWSInstaller(access_key, secret_key, region, az)
    proxy_vm_ids = aws_proxy_data_handler.get_aws_proxy_list()
    for proxy_vm_id in proxy_vm_ids:
        installer.terminate_instance(proxy_vm_id)


if __name__ == '__main__':
    logger.init("ProxyInstall", output=True)
    # install_aws_proxy()

    remove_all_proxys()
