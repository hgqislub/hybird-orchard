import os

from heat.openstack.common import log as logging
import json
import threading
LOG = logging.getLogger(__name__)


def read_conf(file_path):
    fd = None
    try:
        fd = open(file_path, 'r+')
        tmp = fd.read()
        return json.loads(tmp)
    finally:
        if fd:
            fd.close()

def write_conf(file_path, data):
    fd = None
    try:
        fd = open(file_path, 'w+')
        fd.write(json.dumps(data, indent=4))
    finally:
        if fd:
            fd.close()

class CloudInfoHandler:
    def __init__(self, file_path, cloud_id):
        self.file_path = file_path
        self.cloud_id = cloud_id
        self._file_lock = threading.Lock()

    def write_unit_info(self, unit_key, unit_value):
        self._file_lock.acquire()
        try:
            cloud_dict = read_conf(self.file_path)
            if self.cloud_id in cloud_dict.keys():
                cloud_dict[self.cloud_id][unit_key] = unit_value
            else:
                cloud_dict[self.cloud_id] = {unit_key: unit_value}
            write_conf(self.file_path, cloud_dict)
        except Exception as e:
            LOG.error("write unit info error, "
                         "cloud_id: %s, unit_key: %s, unit_value: %s, error: %s"
                         % (self.cloud_id, unit_key, unit_value, e.message))
            raise e
        finally:
            self._file_lock.release()

    def write_cloud_info(self, data):
        self._file_lock.acquire()
        try:
            cloud_dict = read_conf(self.file_path)
            cloud_dict[self.cloud_id] = data
            write_conf(self.file_path, cloud_dict)
        except Exception as e:
            LOG.error("write cloud info error, "
                         "cloud_id: %s,  error: %s"
                         % (self.cloud_id, e.message))
            raise e
        finally:
            self._file_lock.release()

    def get_all_unit_info(self):
        try:
            cloud_dict = read_conf(self.file_path)
        except Exception as e:
            cloud_dict = {}
            LOG.error("get cloud info error, cloud_id: %s, error: %s"
                         % (self.cloud_id, e.message))
        return cloud_dict

    def get_unit_info(self, unit_key):
        cloud_dict = self.get_all_unit_info()
        cloud_info = dict()
        if self.cloud_id in cloud_dict.keys():
            cloud_info = cloud_dict[self.cloud_id]

        if unit_key in cloud_info.keys():
            return cloud_info[unit_key]
        else:
            return None

    def read_cloud_info(self):
        self._file_lock.acquire()
        try:
            cloud_dict = self.get_all_unit_info()
            if self.cloud_id in cloud_dict.keys():
                return cloud_dict[self.cloud_id]
        except Exception as e:
            LOG.error("read hws access cloud error, cloud_id: %s, error: %s"
                         % (self.cloud_id, e.message))
        finally:
            self._file_lock.release()

    def delete_cloud_info(self):
        self._file_lock.acquire()
        try:
            cloud_dict = self.get_all_unit_info()
            if self.cloud_id in cloud_dict.keys():
                cloud_dict.pop(self.cloud_id)
            write_conf(self.file_path, cloud_dict)
        except Exception as e:
            LOG.error("delete hws access cloud error, cloud_id: %s, error: %s"
                         % (self.cloud_id, e.message))
        finally:
            self._file_lock.release()

if __name__ == '__main__':
    read_conf("E:\\test.txt")
    handler = CloudInfoHandler("E:\\test.txt", "cloud1")
    vpn = dict()
    vpn["name"]="hgq1"
    vpn["id"]=1234
    handler.write_unit_info("vpn", vpn)
