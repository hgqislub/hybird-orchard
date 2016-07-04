# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import threading
import os
import json
import log as logger

subnet_data_file = os.path.join("/home/hybrid_cloud/data",
                                "access_cloud_subnet.data")
subnet_manager_lock = threading.Lock()




class SubnetManager(object):
    def __init__(self):
        pass

    def distribute_subnet_pair(self):
        """
        :return:{'api_subnet': '172.29.0.0/24', 'tunnel_subnet': '172.29.1.0/24'}
        """
        subnet_manager_lock.acquire()
        try:
            subnet_info = self.__get_subnet_info__()

            if subnet_info["free"] > 0:
                subnet_id = subnet_info["free_subnet"].pop()
            else:
                subnet_id = subnet_info["total"]
                while subnet_id in subnet_info["free_subnet"] or subnet_id in subnet_info["active_subnet"]:
                    subnet_id += 1

            subnet_info["active_subnet"].append(subnet_id)
            subnet_info["free"] = len(subnet_info["free_subnet"])
            subnet_info["total"] = len(subnet_info["free_subnet"]) + len(subnet_info["active_subnet"])

            self.__write_subnet_info__(subnet_info)

            api_subnet = '172.29.%s.0/24' % subnet_id
            tunnel_subnet = '172.29.%s.0/24' % (subnet_id + 128)

            return {'cloud_api': api_subnet, 'cloud_tunnel': tunnel_subnet}
        except Exception as e:
            logger.error("distribute subnet pair error, error: %s" % e.message)
        finally:
            subnet_manager_lock.release()

    def release_subnet_pair(self, subnet_pair):
        subnet_manager_lock.acquire()
        try:
            api_subnet = subnet_pair['api_subnet']
            tunnel_subnet = subnet_pair['tunnel_subnet']

            api_subnet_id = api_subnet.split(".")[2]
            tunnel_subnet_id = tunnel_subnet.split(".")[2]

            subnet_id = int(api_subnet_id)

            subnet_info = self.__get_subnet_info__()

            if subnet_id in subnet_info["active_subnet"]:
                subnet_info["active_subnet"].remove(subnet_id)
                subnet_info["free_subnet"].append(subnet_id)
                subnet_info["free"] = len(subnet_info["free_subnet"])

            self.__write_subnet_info__(subnet_info)
            return True
        except Exception as e:
            logger.error("release subnet pair error, subnet_pair: %s, error: %s"
                         % (subnet_pair, e.message))
        finally:
            subnet_manager_lock.release()

    @staticmethod
    def __get_subnet_info__():
        if not os.path.exists(subnet_data_file):
            subnet_info = {"free_subnet": [], "active_subnet": [], "total": 0, "free": 0}
        else:
            with open(subnet_data_file, 'r+') as fd:
                tmp = fd.read()
                subnet_info = json.loads(tmp)
        return subnet_info

    @staticmethod
    def __write_subnet_info__(subnet_info):
        with open(subnet_data_file, 'w+') as fd:
            fd.write(json.dumps(subnet_info, indent=4))
