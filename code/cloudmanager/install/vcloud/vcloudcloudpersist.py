# -*- coding:utf-8 -*-


import threading
import os
import json
import logging

from vcloud_cloudinfo import VcloudCloudInfo
from heat.engine.resources.cloudmanager.environmentinfo import *
from heat.engine.resources.cloudmanager.commonutils import *
from heat.openstack.common import log as logging

LOG=logging.getLogger(__name__)

def vcloud_cloud_2_dict(obj):
    result = {}
    result.update(obj.__dict__)
    return result


def dict_2_vcloud_cloud(vcloud_dict):

    vcloud_cloud = VcloudCloudInfo()

    vcloud_cloud.get_exist_cloud(cloud_id=vcloud_dict["cloud_id"],
                         vcloud_url=vcloud_dict["vcloud_url"],
                         vcloud_org=vcloud_dict["vcloud_org"],
                         vcloud_vdc=vcloud_dict["vcloud_vdc"],
                         vcloud_edgegw=vcloud_dict["vcloud_edgegw"],
                         username=vcloud_dict["username"],
                         passwd=vcloud_dict["passwd"],
                         region_name=vcloud_dict["region_name"],
                         availabilityzone=vcloud_dict["availabilityzone"],
                         azname=vcloud_dict["azname"],
                         cascaded_domain=vcloud_dict["cascaded_domain"],
                         cascaded_eip=vcloud_dict["cascaded_eip"],
                         vpn_eip=vcloud_dict["vpn_eip"],
                         cloud_proxy=vcloud_dict["cloud_proxy"],
                         driver_type=vcloud_dict["driver_type"],
                         access=vcloud_dict["access"],
                         with_ceph=vcloud_dict["with_ceph"])


    return vcloud_cloud


vcloud_cloud_data_file = os.path.join("/home/hybrid_cloud/data/vcloud",
                                   "vcloud_access_cloud.data")
vcloud_cloud_data_file_lock = threading.Lock()


class VcloudCloudInfoPersist(object):
    def __init__(self):
        pass

    def list_vcloud_clouds(self):
        cloud_dicts = self.__read_vcloud_cloud_info__()
        return cloud_dicts.keys()

    def get_vcloud_cloud(self, cloud_id):
        cloud_dicts = self.__read_vcloud_cloud_info__()
        if cloud_id in cloud_dicts.keys():
            return dict_2_vcloud_cloud(cloud_dicts[cloud_id])
        else:
            return None

    def delete_vcloud_cloud(self, cloud_id):
        vcloud_cloud_data_file_lock.acquire()
        try:
            cloud_dicts = self.__read_vcloud_cloud_info__()
            cloud_dicts.pop(cloud_id)
            self.__write_vcloud_cloud_info__(cloud_dicts)
        except Exception as e:
            LOG.error("delete vcloud cloud data file error, "
                         "cloud_id: %s, error: %s"
                         % (cloud_id, e.message))
        finally:
            vcloud_cloud_data_file_lock.release()

    def add_vcloud_cloud(self, vcloud_cloud):
        vcloud_cloud_data_file_lock.acquire()
        try:
            cloud_dicts = self.__read_vcloud_cloud_info__()
            dict_temp = vcloud_cloud_2_dict(vcloud_cloud)
            cloud_dicts[vcloud_cloud.cloud_id] = dict_temp
            self.__write_vcloud_cloud_info__(cloud_dicts)
        except Exception as e:
            LOG.error("add vcloud cloud data file error, "
                         "vcloud_cloud: %s, error: %s"
                         % (vcloud_cloud, e.message))
        finally:
            vcloud_cloud_data_file_lock.release()

    @staticmethod
    def __read_vcloud_cloud_info__():
        if not os.path.exists(vcloud_cloud_data_file):
            LOG.error("read %s : No such file." % vcloud_cloud_data_file)
            cloud_dicts = {}
        else:
            with open(vcloud_cloud_data_file, 'r+') as fd:
                cloud_dicts = json.loads(fd.read())
        return cloud_dicts

    @staticmethod
    def __write_vcloud_cloud_info__(cloud_dicts):
        with open(vcloud_cloud_data_file, 'w+') as fd:
            fd.write(json.dumps(cloud_dicts, indent=4))
