# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import threading

from awscloud import AwsCloud
from heat.engine.resources.cloudmanager.util.commonutils import *


def aws_cloud_2_dict(obj):
    result = {}
    result.update(obj.__dict__)
    return result


def dict_2_aws_cloud(aws_dict):
    aws_cloud = AwsCloud(cloud_id=aws_dict["cloud_id"],
                         access_key=aws_dict["access_key"],
                         secret_key=aws_dict["secret_key"],
                         region_name=aws_dict["region_name"],
                         az=aws_dict["az"],
                         az_alias=aws_dict["az_alias"],
                         cascaded_domain=aws_dict["cascaded_domain"],
                         cascaded_eip=aws_dict["cascaded_eip"],
                         vpn_eip=aws_dict["vpn_eip"],
                         cloud_proxy=aws_dict["cloud_proxy"],
                         driver_type=aws_dict["driver_type"],
                         access=aws_dict["access"],
                         with_ceph=aws_dict["with_ceph"])
    return aws_cloud


aws_cloud_data_file = os.path.join("/home/hybrid_cloud/data",
                                   "aws_access_cloud.data")
aws_cloud_data_file_lock = threading.Lock()


class AwsCloudDataHandler(object):
    def __init__(self):
        pass

    def list_aws_clouds(self):
        cloud_dicts = self.__read_aws_cloud_info__()
        return cloud_dicts.keys()

    def get_aws_cloud(self, cloud_id):
        cloud_dicts = self.__read_aws_cloud_info__()
        if cloud_id in cloud_dicts.keys():
            return dict_2_aws_cloud(cloud_dicts[cloud_id])
        else:
            return None

    def delete_aws_cloud(self, cloud_id):
        aws_cloud_data_file_lock.acquire()
        try:
            cloud_dicts = self.__read_aws_cloud_info__()
            cloud_dicts.pop(cloud_id)
            self.__write_aws_cloud_info__(cloud_dicts)
        except Exception as e:
            logger.error("delete aws cloud data file error, "
                         "cloud_id: %s, error: %s"
                         % (cloud_id, e.message))
        finally:
            aws_cloud_data_file_lock.release()

    def add_aws_cloud(self, aws_cloud):
        aws_cloud_data_file_lock.acquire()
        try:
            cloud_dicts = self.__read_aws_cloud_info__()
            dict_temp = aws_cloud_2_dict(aws_cloud)
            cloud_dicts[aws_cloud.cloud_id] = dict_temp
            self.__write_aws_cloud_info__(cloud_dicts)
        except Exception as e:
            logger.error("add aws cloud data file error, "
                         "aws_cloud: %s, error: %s"
                         % (aws_cloud, e.message))
        finally:
            aws_cloud_data_file_lock.release()

    @staticmethod
    def __read_aws_cloud_info__():
        if not os.path.exists(aws_cloud_data_file):
            logger.error("read %s : No such file." % aws_cloud_data_file)
            cloud_dicts = {}
        else:
            with open(aws_cloud_data_file, 'r+') as fd:
                cloud_dicts = json.loads(fd.read())
        return cloud_dicts

    @staticmethod
    def __write_aws_cloud_info__(cloud_dicts):
        with open(aws_cloud_data_file, 'w+') as fd:
            fd.write(json.dumps(cloud_dicts, indent=4))
