# -*- coding:utf-8 -*-

__author__ = 'q00222219@huawei'

import os
import threading
import log as logger
import json

_aws_proxy_data_file = os.path.join("/home/hybrid_cloud/data",
                                    "aws_proxy.data")
_aws_proxy_data_file_lock = threading.Lock()


def _read_aws_proxy_info():
    aws_proxy_info = {"proxys": []}
    if not os.path.exists(_aws_proxy_data_file):
        logger.error("read %s : No such file." % _aws_proxy_data_file)

    else:
        with open(_aws_proxy_data_file, 'r+') as fd:
            try:
                aws_proxy_info = json.loads(fd.read())
            except:
                pass
    return aws_proxy_info


def _write_aws_proxy_info(aws_proxy_info):
    with open(_aws_proxy_data_file, 'w+') as fd:
        fd.write(json.dumps(aws_proxy_info, indent=4))


def add_new_proxy(proxy_vm_id):
    aws_proxy_info = _read_aws_proxy_info()
    proxys = aws_proxy_info["proxys"]
    proxys.append(proxy_vm_id)
    _write_aws_proxy_info(aws_proxy_info)


def get_aws_proxy_list():
    aws_proxy_info = _read_aws_proxy_info()
    return aws_proxy_info["proxys"]
