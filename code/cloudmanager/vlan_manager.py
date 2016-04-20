# -*- coding:utf-8 -*-

__author__ = 'q00222219@huawei'


import threading
import os
import json
import log as logger

_vlan_data_file = os.path.join("/home/hybrid_cloud/data",
                               "access_cloud_vlan.data")
_vlan_manager_lock = threading.Lock()

_START_VLAN = 4010


def allocate_vlan():
    _vlan_manager_lock.acquire()
    try:
        vlan_info = _get_vlan_info()

        if len(vlan_info["free_vlan"]) > 0:
            vlan = vlan_info["free_vlan"].pop()
            vlan_info["active_vlan"].append(vlan)
        else:
            vlan = _START_VLAN + len(vlan_info["active_vlan"])
            vlan_info["active_vlan"].append(vlan)

        _write_vlan_info(vlan_info)
        return vlan
    except Exception as e:
        logger.error("allocate vlan error, error: %s" % e.message)
    finally:
        _vlan_manager_lock.release()


def release_vlan(vlan):
    _vlan_manager_lock.acquire()
    try:
        vlan_info = _get_vlan_info()

        if vlan in vlan_info["active_vlan"]:
            vlan_info["active_vlan"].pop(vlan)

        if vlan not in vlan_info["free_vlan"]:
            vlan_info["free_vlan"].append(vlan)

        _write_vlan_info(vlan_info)
        return True
    except Exception as e:
        logger.error("release vlan error, vlan: %s, error: %s"
                     % (vlan, e.message))
        return False
    finally:
        _vlan_manager_lock.release()


def _get_vlan_info():
    subnet_info = {"free_vlan": [], "active_vlan": []}
    if os.path.exists(_vlan_data_file):
        with open(_vlan_data_file, 'r+') as fd:
            try:
                subnet_info = json.loads(fd.read())
            except:
                pass
    return subnet_info


def _write_vlan_info(vlan_info):
    with open(_vlan_data_file, 'w+') as fd:
        fd.write(json.dumps(vlan_info, indent=4))