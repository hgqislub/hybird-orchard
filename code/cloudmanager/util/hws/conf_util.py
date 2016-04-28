import os

from heat.openstack.common import log as logging
import json
import threading
LOG = logging.getLogger(__name__)
_file_lock = threading.Lock()

def read_conf(file_path):
    try:
        with open(file_path, 'r+') as fd:
            tmp = fd.read()
            return json.loads(tmp)
    finally:
        if fd:
            fd.close()

def write_conf(file_path, data):
    try:
        with open(file_path, 'w+') as fd:
            fd.write(json.dumps(data, indent=4))
    finally:
        if fd:
            fd.close()

class CloudInfoHandler:
    def __init__(self, file_path, cloud_id):
        self.file_path = file_path
        self.cloud_id = cloud_id
    def write_unit_info(self, unit_key, unit_value):
        _file_lock.acquire()
        try:
            cloud_dict = read_conf(self.file_path)
            if self.cloud_id in cloud_dict.keys():
                cloud_dict[self.cloud_id][unit_key] = unit_value
            else:
                cloud_dict[self.cloud_id] = {unit_key: unit_value}
            write_conf(self.file_path, cloud_dict)
        except Exception as e:
            LOG.error("write access cloud unit info error, "
                         "cloud_id: %s, unit_key: %s, unit_value: %s, error: %s"
                         % (self.cloud_id, unit_key, unit_value, e.message))
        finally:
            _file_lock.release()