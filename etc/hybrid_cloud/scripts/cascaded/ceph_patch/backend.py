'''
@author: luobin
'''
import sys
import os
import json
from time import sleep
from constant import BackendConstant

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append('/usr/bin/')

from install_tool import cps_server
import log as LOG

BACKEND_NAME = BackendConstant.BACKEND_NAME
CEPH_STORAGE_BACKEND = BackendConstant.CEPH_STORAGE_BACKEND
CEPH_VOLUME_PREFIX = BackendConstant.CEPH_VOLUME_PREFIX

class Backend(object):
    
    def __init__(self):
        pass

    def _get_update_ceph_param(self, update_key, update_val):
        params = cps_server.get_template_params("cinder", "cinder-volume")
        if params['cfg']['other_storage_cfg'] == '' or params['cfg']['other_storage_cfg'] == {}:
            other_storage_cfg = dict()
        else:
            other_storage_cfg = json.loads(json.dumps(params['cfg']['other_storage_cfg']))
    
        if params['cfg']['driver_data'] == '' or params['cfg']['driver_data'] == {}:
            driver_data = dict()
            # next_index = 0
        else:
            driver_data = json.loads(json.dumps(params['cfg']['driver_data']))
            # next_index = int(max(driver_data.items(),key=lambda x:int(x[0]))[0]) + 1
        
        for key, val in driver_data.items():
            if val["backend_name"] == BACKEND_NAME:
                other_storage_cfg[str(key)][CEPH_STORAGE_BACKEND][update_key] = json.loads(json.dumps(update_val))
        
        update_param = {"other_storage_cfg": json.loads(json.dumps(other_storage_cfg))}
    
        return update_param

    def update_ceph_param(self, key, val):
        LOG.info("update ceph backend: %s = %s" % (key, val))
        update_param = self._get_update_ceph_param(key, val)
        LOG.info("cps_server update cinder cinder-volume")
        while True:
            if not cps_server.update_template_params("cinder", "cinder-volume", update_param):
                sleep(5)
                continue
            else:
                break
        LOG.info("cps_server update cinder cinder-backup")
        while True:
            if not cps_server.update_template_params("cinder", "cinder-backup", update_param):
                sleep(5)
                continue
            else:
                break
        self._commit()
    '''
    def _get_update_param(self, update_params):
        params = cps_server.get_template_params("cinder", "cinder-volume")
        if params['cfg']['other_storage_cfg'] == '' or params['cfg']['other_storage_cfg'] == {}:
            other_storage_cfg = dict()
        else:
            other_storage_cfg = json.loads(json.dumps(params['cfg']['other_storage_cfg']))

        if params['cfg']['driver_data'] == '' or params['cfg']['driver_data'] == {}:
            driver_data = dict()
            # next_index = 0
        else:
            driver_data = json.loads(json.dumps(params['cfg']['driver_data']))
            # next_index = int(max(driver_data.items(),key=lambda x:int(x[0]))[0]) + 1

        for key, val in driver_data.items():
            if val["backend_name"] == BACKEND_NAME:
                for update_key, update_val in update_params:
                    other_storage_cfg[str(key)][CEPH_STORAGE_BACKEND][update_key] = json.loads(json.dumps(update_val))

        update_param = {"other_storage_cfg": json.loads(json.dumps(other_storage_cfg))}

        return update_param

    def update_ceph_params(self, update_params):
        LOG.info("update ceph backend: %s " % update_params)
        update_param = self._get_update_ceph_param(update_params)
        LOG.info("cps_server update cinder cinder-volume")
        while True:
            if not cps_server.update_template_params("cinder", "cinder-volume", update_param):
                sleep(5)
                continue
            else:
                break
        LOG.info("cps_server update cinder cinder-backup")
        while True:
            if not cps_server.update_template_params("cinder", "cinder-backup", update_param):
                sleep(5)
                continue
            else:
                break
        self._commit()
    '''

    def _commit(self):
        LOG.info("cps_server cps_commit")
        cps_server.cps_commit()

