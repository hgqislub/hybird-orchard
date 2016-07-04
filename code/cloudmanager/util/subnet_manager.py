# -*- coding:utf-8 -*-
__author__ = 'l00293089@huawei'

import threading
import os
import json
from heat.openstack.common import log as logging

LOG = logging.getLogger(__name__)

subnet_manager_lock = threading.Lock()

SUBNET_ID_MAX=128

class SubnetManager(object):
    def __init__(self):
        pass

    def distribute_subnet_pair(self, api_cidr, tunnel_cidr, data_file):
        subnet_manager_lock.acquire()

        try:
            subnet_info = self.__get_subnet_info__(data_file)
            subnet_id = 0
            for free_id in range(SUBNET_ID_MAX):
                if free_id in subnet_info["allocate"]:
                    continue
                else:
                    subnet_id = free_id
                    break
            if subnet_id == 0:
                LOG.error("no more subnet can be allocate")
                return None

            subnet_info["allocate"].append(subnet_id)

            api_subnet = ".".join([ api_cidr.split('.')[0], api_cidr.split('.')[1], '%s', api_cidr.split('.')[3] ])
            tunnel_subnet = ".".join([ tunnel_cidr.split('.')[0], tunnel_cidr.split('.')[1], '%s', tunnel_cidr.split('.')[3] ])

            api_subnet = api_subnet % subnet_id
            tunnel_subnet = tunnel_subnet % (subnet_id+128)

            self.__write_subnet_info__(subnet_info, data_file)

            return {'external_api_cidr': api_subnet, 'tunnel_bearing_cidr': tunnel_subnet}

        except Exception as e:
            LOG.error("distribute subnet pair error, error: %s" % e.message)
        finally:
            subnet_manager_lock.release()

    def release_subnet_pair(self, subnet_pair, data_file):
        subnet_manager_lock.acquire()
        try:
            api_subnet = subnet_pair['external_api_cidr']

            api_subnet_id = api_subnet.split(".")[2]

            subnet_id = int(api_subnet_id)

            subnet_info = self.__get_subnet_info__(data_file)

            if subnet_id in subnet_info["allocate"]:
                subnet_info["allocate"].remove(subnet_id)

            self.__write_subnet_info__(subnet_info, data_file)
            return True
        except Exception as e:
            LOG.error("release subnet pair error, subnet_pair: %s, error: %s"
                         % (subnet_pair, e.message))
        finally:
            subnet_manager_lock.release()

    @staticmethod
    def __get_subnet_info__(subnet_data_file):
        if not os.path.exists(subnet_data_file):
            subnet_info = {"allocate":[]}
        else:
            with open(subnet_data_file, 'r+') as fd:
                tmp = fd.read()
                subnet_info = json.loads(tmp)["subnet_info"]
        return subnet_info

    @staticmethod
    def __write_subnet_info__(subnet_info, subnet_data_file):
        with open(subnet_data_file, 'w+') as fd:
            fd.write(json.dumps(subnet_info, indent=4))
