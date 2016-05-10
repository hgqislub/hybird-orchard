
import sys
sys.path.append('..')

import os
import pdb
from heat.openstack.common import log as logging
import util.vcloud.vcloud_install as vcloudinstaller
import util.hws.hws_install as hws_installer
import util.hws.hws_cloudinfo as hws_cloudinfo
import util.hws.hws_config as hws_config

import util.vcloud.vcloud_cloudinfo as vcloudcloudinfo
import util.vcloud.vcloud_config as vcloudconfiger
from util.vcloud.vcloudcloudpersist import VcloudCloudDataHandler


#from subnet_manager import SubnetManager
import proxy_manager

LOG = logging.getLogger(__name__)


class CloudManager:
    def __init__(self,cloud_params):
        self.cloud_type = cloud_params['cloud_type']
        self.cloud_params = cloud_params
        self.cloud_installer = SubCloud(self.cloud_params)

    def add_cloud(self):
        
        #serviceinstaller = AddServie()


        if self.cloud_type != 'FS':
          #deploy proxy
          proxy_info = self.cloud_installer.deploy_proxy()

          #preinstall
          self.cloud_installer.cloud_preinstall()

          self.cloud_installer.cloud_install()    #deploy cascaded and vpn

          #initialize the cloud params
          install_info = self.cloud_installer.package_installinfo()
          self.cloud_installer.cloudinfo.initialize(self.cloud_params, install_info, proxy_info, self.cloud_installer.installer)
          self.cloud_installer.configer.initialize(self.cloud_params, install_info, proxy_info, self.cloud_installer.cloudinfo, self.cloud_installer.installer)

        self.cloud_installer.cloud_postinstall(self.cloud_installer.cloudinfo)    #postinstall

        #register cloud information
        self.cloud_installer.register_cloud()

    def delete_cloud(self):

        #get cloud id
        cloud_id = "@".join([self.cloud_params['vcloud_url'],self.cloud_params['vcloud_org'],
                                  self.cloud_params['vcloud_vdc'], self.cloud_params['region_name'],
                                  self.cloud_params['azname']])

        cloudinstaller = SubCloud(self.cloud_params)    #initialize param
        install_info = cloudinstaller.installer.get_vcloud_access_cloud_install_info(installer=cloudinstaller.installer)
        cloudinstaller.cloudinfo = cloudinstaller.installer.get_vcloud_cloud()
        cloudinstaller.configer.initialize(self.cloud_params, install_info, cloudinstaller.cloudinfo.cloud_proxy, cloudinstaller.cloudinfo, cloudinstaller.installer)

        cloudinstaller.cloud_uninstall()    #uninstall

        cloudinstaller.cloud_postuninstall()    #postuninstall

        cloudinstaller.unregister_cloud()   #unregister cloud information

    def list_cloud(self):
        pass

    def update_cloud(self):
        pass

    def add_service(self):
        cloud_id = "@".join([self.cloud_params['vcloud_org'], self.cloud_params['vcloud_vdc'],
                             self.cloud_params['region_name'], self.cloud_params['azname']])    #get cloud id


        serviceinstaller = Service(self.cloud_params)    #initialize param
        install_info = serviceinstaller.installer.get_vcloud_access_cloud_install_info(installer=serviceinstaller.installer)
        serviceinstaller.cloudinfo = serviceinstaller.installer.get_vcloud_cloud()
        serviceinstaller.configer.initialize(self.cloud_params, install_info, serviceinstaller.cloudinfo.cloud_proxy, cloudinstaller.cloudinfo, cloudinstaller.installer)

        serviceinstaller.service_preinstall()

        serviceinstaller.service_install()

        serviceinstaller.service_postuninstall()

        serviceinstaller.register_cloud()

    def delete_service(self):
        pass

    def add_vpn_only(self):
        cloudinstaller = SubCloud(self.cloud_params)

        cloudinstaller.cloud_preinstall()    #preinstall

        cloudinstaller.deploy_vpn()    #deploy cascaded and vpn

        install_info = cloudinstaller.package_installinfo()    #initialize the cloud params
        cloudinstaller.cloudinfo.initialize(self.cloud_params, install_info, None, cloudinstaller.installer)
        cloudinstaller.configer.initialize(self.cloud_params, install_info, None, cloudinstaller.cloudinfo, cloudinstaller.installer)

        cloudinstaller.cloud_postinstall(cloudinstaller.cloudinfo)    #postinstall

        cloudinstaller.config_vpn_only()

    def delete_vpn_only(self):
        cloud_id = "@".join([self.cloud_params['vcloud_org'], self.cloud_params['vcloud_vdc'],
                             self.cloud_params['region_name'], self.cloud_params['azname']])    #get cloud id

        cloudinstaller = SubCloud(self.cloud_params)    #initialize param
        install_info = cloudinstaller.installer.get_vcloud_access_cloud_install_info(installer=cloudinstaller.installer)
        cloudinstaller.cloudinfo = cloudinstaller.installer.get_vcloud_cloud()
        cloudinstaller.configer.initialize(self.cloud_params, install_info, None, cloudinstaller.cloudinfo, cloudinstaller.installer)

        cloudinstaller.delete_vpn()    #uninstall

        cloudinstaller.cloud_postuninstall()    #postuninstall

class SubCloud(object):
    def __init__(self, cloud_params):
        self.cloud_type = cloud_params['cloud_type']
        self.installer = None
        self.configer = None
        self.cloudinfo = None
        self.init_installer(cloud_params)

    def init_installer(self, cloud_params):

        if self.cloud_type == 'VCLOUD':
            self.installer = vcloudinstaller.VcloudCloudInstaller(cloud_params=cloud_params)
            self.configer = vcloudconfiger.VcloudCloudConfig()
            self.cloudinfo = vcloudcloudinfo.VcloudCloudInfo()
        if self.cloud_type == 'HWS':
            self.installer = hws_installer.HwsCascadedInstaller(cloud_params=cloud_params)
            self.cloudinfo = hws_cloudinfo.HwsCloudInfo()
            self.configer = hws_config.HwsConfig()

    def cloud_preinstall(self):
        self.installer.cloud_preinstall()

    def cloud_postinstall(self,cloud_info):
        self.installer.cloud_postinstall(cloud_info)

    def cloud_postuninstall(self):
        self.installer.cloud_postuninstall()

    def package_installinfo(self):
        return self.installer.package_installinfo()

    @staticmethod
    def deploy_proxy():
        return proxy_manager.distribute_proxy()

    def delete_proxy(self):
        pass

    def deploy_vpn(self):
        self.installer.install_vpn()

    def delete_vpn(self):
        self.installer.uninstall_vpn()

    def cloud_install(self):
        self.installer.cloud_install()

    def cloud_uninstall(self):
        self.installer.cloud_uninstall()

    def config_vpn_only(self):
        self.configer.config_vpn_only()

    def register_cloud(self):
        self.configer.config_vpn()
        pdb.set_trace()
        self.configer.config_cascading()
        pdb.set_trace()
        self.configer.config_cascaded()
        pdb.set_trace()
        self.configer.config_route()
        pdb.set_trace()
        self.configer.config_proxy()
        pdb.set_trace()
        self.configer.config_patch()
        pdb.set_trace()
        self.configer.config_storge()
        #self.configer.config_extnet()

    def unregister_cloud(self):
        self.configer.remove_existed_cloud()


class Service(object):
    def __init__(self,cloud_params):
        self.cloud_type = cloud_params['cloud_type']
        self.installer = None
        self.configer = None
        self.cloudinfo = None
        self.init_installer(cloud_params)

    def init_installer(self,cloud_params):
        if(self.cloud_type == 'VCLOUD'):
            self.installer =  vcloudinstaller.VcloudCloudInstaller(cloud_params=cloud_params)
            self.configer = vcloudconfiger.VcloudCloudConfig()
            self.cloudinfo = vcloudcloudinfo.VcloudCloudInfo()

    def service_preinstall(self):
        self.installer.cloud_preinstall()

    def service_install(self):
        self.installer.service_install()

    def service_postuninstall(self):
        self.installer.service_postuninstall()

    def register_cloud(self):
        self.configer.config_service()









