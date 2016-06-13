
import sys
sys.path.append('..')

import os
import pdb
from heat.openstack.common import log as logging
import install.hws.hws_install as hws_installer
import install.hws.hws_config as hws_config

LOG = logging.getLogger(__name__)

class CloudManager:
    def __init__(self,cloud_params):         
        self.cloud_params = cloud_params
        self.cloud_installer = Cloud(cloud_params)        

    def add_cloud(self):        
        self.cloud_installer.cloud_preinstall()    #preinstall
        self.cloud_installer.cloud_install()    #deploy cascaded and vpn        
        self.cloud_installer.cloud_postinstall()    #postinstal 

    def delete_cloud(self):                   
        self.cloud_installer.cloud_preuninstall()    #preinstall
        self.cloud_installer.cloud_uninstall()    #uninstall
        self.cloud_installer.cloud_postuninstall()    #postuninstall

    def list_cloud(self):
        pass

    def update_cloud(self):
        pass
    
class Cloud(object):
    def __init__(self,cloud_params):
        self.cloud_params = cloud_params
        self.cloud_type = cloud_params['cloud_type']
        self.installer = None
        self.configer = None
        self.init_installer(cloud_params)

    def init_installer(self,cloud_params):
        if self.cloud_type == 'HWS':
            self.installer = \
                hws_installer.HwsCascadedInstaller(cloud_params=cloud_params)
            self.configer = hws_config.HwsConfig()

    def cloud_preinstall(self):
        self.installer.cloud_preinstall()

    def cloud_postinstall(self):
        self.installer.cloud_postinstall()

    def cloud_postuninstall(self):
        self.installer.cloud_postuninstall()

    def package_install_info(self):
        return self.installer.package_install_info()
 
    def cloud_install(self):
        self.installer.cloud_install()

        cloud_info = self.installer.package_cloud_info()
        self.configer.initialize(self.cloud_params, cloud_info)
        self.register_cloud()

    def cloud_preuninstall(self):
        self.installer.cloud_preuninstall()
        pass
    def cloud_uninstall(self):
        install_info = self.installer.get_cloud_info()
        self.installer.cloud_uninstall()   
        self.configer.install_info = install_info
        self.unregister_cloud()   #unregister cloud information
  
    def get_cloud_info(self):
        self.installer.get_cloud_info()

    def register_cloud(self):
        self.configer.config_vpn()
        self.configer.config_cascading()
        self.configer.config_cascaded()
        self.configer.config_route()
        self.configer.config_proxy()
        self.configer.config_patch()
        self.configer.config_storge()
        #self.configer.config_extnet()

    def unregister_cloud(self):
        self.configer.remove_existed_cloud()










