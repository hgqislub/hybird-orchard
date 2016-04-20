'''
@author: luobin
'''

import sys
import os
import traceback
import json
from time import sleep

sys.path.append('/usr/bin/')
from install_tool import cps_server
import log as LOG

class RefCPSService():
    @staticmethod
    def get_cps_http(url):
        return cps_server.get_cps_http(url)
    @staticmethod
    def post_cps_http(url, body):
        return cps_server.post_cps_http(url, body)

class RefCPSServiceExtent():
    @staticmethod
    def list_template_instance(service, template):
        url = '/cps/v1/instances?service=%s&template=%s' % (service, template)
        res_text = RefCPSService.get_cps_http(url)
        if not res_text is None:
            return json.loads(res_text)
        return None
    
    @staticmethod
    def host_template_instance_operate(service, template, action):
        url = '/cps/v1/instances?service=%s&template=%s' % (service, template)
        body = {'action': action}
        return RefCPSService.post_cps_http(url, body)

class CPSParamsUpdate():
    @staticmethod
    def cps_server_update_params_list(service_name, template_name, update_params_list):
        while len(update_params_list) != 0:
            update_params_item = update_params_list.pop()
        
            if not cps_server.update_template_params(service_name, template_name, update_params_item):
                LOG.error("update service %s template %s params failed."%(service_name,template_name))
                update_params_list.append(update_params_item)
                sleep(5)
            else:
                LOG.info("update service %s template %s params successed."%(service_name,template_name))
        cps_server.cps_commit()

def restart_component(service_name, template_name):
    ret = RefCPSServiceExtent.host_template_instance_operate(service_name, template_name, 'stop')
    if not ret:
        LOG.error("cps template_instance_action stop for %s failed." % template_name)
        return ret
    ret = RefCPSServiceExtent.host_template_instance_operate(service_name, template_name, 'start')
    if not ret:
        LOG.error("cps template_instance_action start for %s failed." % template_name)
        return ret
