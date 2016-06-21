# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import sys
sys.path.append('/usr/bin/install_tool')
from heat.openstack.common import log as logging
import log as logger
import cps_server
import threading
import install.aws_proxy_install as aws_installer

proxy_manager_lock = threading.Lock()


LOG = logging.getLogger(__name__)

logger.init('CloudManager')

def distribute_proxy():
    proxy_manager_lock.acquire()
    try:
        host_list = cps_server.cps_host_list()
        hosts = host_list["hosts"]
        free_proxy_list = []
        allocated_proxy_nums = []

        for host in hosts:
            proxy_info = {"id": host["id"],
                          "status": host["status"],
                          "manageip": host["manageip"]
                          }

            # proxy_free = True
            # for role in host["roles"]:
            #     if "compute-proxy" in role:
            #         num = role.split("-")[1]
            #         allocated_proxy_nums.append(num)
            #         proxy_free = False
            #         break
            #
            # if proxy_free:
            #     free_proxy_list.append(proxy_info)

            if len(host["roles"]) <= 2 and "normal" == host["status"]:
                free_proxy_list.append(proxy_info)
            else:
                for role in host["roles"]:
                    if "compute-proxy" in role:
                        num = role.split("-")[1]
                        allocated_proxy_nums.append(num)

        if 0 == len(free_proxy_list):
            return None

        right_proxy = free_proxy_list[0]
        num = 1

        while True:
            right_proxy_num = "proxy" + str(num).zfill(3)
            if right_proxy_num not in allocated_proxy_nums:
                right_proxy["proxy_num"] = right_proxy_num
                break
            else:
                num += 1

        # add role for this proxy
        # _add_role_to_proxy(right_proxy["id"], right_proxy["proxy_num"])

        return right_proxy
    except Exception as e:
        LOG.error("distribute proxy error, error: %s" % e.message)
    finally:
        proxy_manager_lock.release()


def _add_role_to_proxy(proxy_id, proxy_num):
    dhcp_role_name = "dhcp"
    cps_server.role_host_add(dhcp_role_name, [proxy_id])

    compute_proxy_role_name = '-'.join(["compute", proxy_num])
    cps_server.role_host_add(compute_proxy_role_name, [proxy_id])

    network_proxy_role_name = '-'.join(["network", proxy_num])

    cps_server.role_host_add(network_proxy_role_name, [proxy_id])

    blockstorage_proxy_role_name = '-'.join(["blockstorage", proxy_num])
    cps_server.role_host_add(blockstorage_proxy_role_name, [proxy_id])

    cps_server.cps_commit

if __name__ == '__main__':
    print distribute_proxy()
