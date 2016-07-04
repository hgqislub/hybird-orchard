# -*- coding:utf-8 -*-


import sys
sys.path.append("..")

import os
import threading
from heat.openstack.common import log as logging
import json

LOG=logging.getLogger(__name__)

_vcloud_proxy_data_file = os.path.join("/home/hybrid_cloud/data",
                                    "vcloud_proxy.data")
_vcloud_proxy_data_file_lock = threading.Lock()


def _read_vcloud_proxy_info():
    vcloud_proxy_info = {"proxys": []}
    if not os.path.exists(_vcloud_proxy_data_file):
        LOG.error("read %s : No such file." % _vcloud_proxy_data_file)

    else:
        with open(_vcloud_proxy_data_file, 'r+') as fd:
            try:
                vcloud_proxy_info = json.loads(fd.read())
            except:
                pass
    return vcloud_proxy_info


def _write_vcloud_proxy_info(vcloud_proxy_info):
    with open(_vcloud_proxy_data_file, 'w+') as fd:
        fd.write(json.dumps(vcloud_proxy_info, indent=4))


def add_new_proxy(proxy_vm_id):
    vcloud_proxy_info = _read_vcloud_proxy_info()
    proxys = vcloud_proxy_info["proxys"]
    proxys.append(proxy_vm_id)
    _read_vcloud_proxy_info(vcloud_proxy_info)


def get_vcloud_proxy_list():
    vcloud_proxy_info = _read_vcloud_proxy_info()
    return vcloud_proxy_info["proxys"]
