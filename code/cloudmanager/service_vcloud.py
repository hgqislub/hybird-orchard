
import sys
sys.path.append('..')

import os
import pdb
from heat.openstack.common import log as logging
import util.vcloud.vcloud_install as vcloudinstaller
import util.hwscloud.hwscloud_install as hwscloudinstaller
import util.vcloud.vcloud_cloudinfo as vcloudcloudinfo
import util.vcloud.vcloud_config as vcloudconfiger
from util.vcloud.vcloudcloudpersist import VcloudCloudDataHandler


from subnet_manager import SubnetManager
import proxy_manager

LOG = logging.getLogger(__name__)


class CloudManager:
    def __init__(self,cloud_params):
        self.cloud_type = cloud_params['cloud_type']
        self.cloud_params = cloud_params
        

    def add_cloud(self):
        cloudinstaller = SubCloud(self.cloud_params)
        #serviceinstaller = AddServie()


        if(self.cloud_type != 'FS'):
          #deploy proxy
          proxy_info = cloudinstaller.deploy_proxy()

          #preinstall
          cloudinstaller.cloud_preinstall()

          #deploy cascaded and vpn
          cloudinstaller.deploy_cascaded()
          cloudinstaller.deploy_vpn()

          #initialize the cloud params
          install_info = cloudinstaller.package_installinfo()
          cloudinstaller.cloudinfo.initialize(self.cloud_params, install_info, proxy_info, cloudinstaller.installer)
          cloudinstaller.configer.initialize(self.cloud_params, install_info, proxy_info, cloudinstaller.cloudinfo, cloudinstaller.installer)

          # if(self.cloud_params['service'] == ?)
          #   serviceinstaller.deploy_service('v2v')
          #   serviceinstaller.deploy_service('ceph')

        #postinstall
        cloudinstaller.cloud_postinstall(cloudinstaller.cloudinfo)

        #register cloud information
        cloudinstaller.register_cloud()

    def delete_cloud(self):

        #get cloud id
        cloud_id = "@".join([self.cloud_params['vcloud_url'],self.cloud_params['vcloud_org'],
                                  self.cloud_params['vcloud_vdc'], self.cloud_params['region_name'],
                                  self.cloud_params['azname']])

        #initialize param
        cloudinstaller = SubCloud(self.cloud_params)
        install_info = cloudinstaller.installer.get_vcloud_access_cloud_install_info(installer=cloudinstaller.installer)
        cloudinstaller.cloudinfo = VcloudCloudDataHandler().get_vcloud_cloud(cloud_id=cloud_id)
        cloudinstaller.configer.initialize(self.cloud_params, install_info, cloudinstaller.cloudinfo.cloud_proxy, cloudinstaller.cloudinfo, cloudinstaller.installer)

        #uninstall
        cloudinstaller.delete_cascaded()
        cloudinstaller.delete_vpn()
        cloudinstaller.cloud_postuninstall()

        #unregister cloud information
        cloudinstaller.unregister_cloud()

    def list_cloud(self):
        pass

    def update_cloud(self):
        pass


class SubCloud(object):
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
        if(self.cloud_type == 'HWCLOUD'):
            self.installer =  hwscloudinstaller.VcloudCloudInstaller(cloud_params=cloud_params)
            self.configer = hwscloudinstaller.VcloudCloudConfig()
            self.cloudinfo = hwscloudinstaller.VcloudCloudInfo()



    def cloud_preinstall(self):
        self.installer.cloud_preinstall()

    def cloud_postinstall(self,cloud_info):
        self.installer.cloud_postinstall(cloud_info)

    def cloud_postuninstall(self):
        self.installer.cloud_postuninstall()

    def package_installinfo(self):
        return self.installer.package_installinfo()

    def deploy_proxy(self):
        return proxy_manager.distribute_proxy()

    def delete_proxy(self):
        pass

    def deploy_cascaded(self):
        self.installer.install_cascaded()

    def delete_cascaded(self):
        self.installer.uninstall_cascaded()

    def deploy_vpn(self):
        self.installer.install_vpn()

    def delete_vpn(self):
        self.installer.uninstall_vpn()



    def register_cloud(self):
        self.configer.config_vpn()
        self.configer.config_cascading()
        self.configer.config_cascaded()
        self.configer.config_proxy()
        self.configer.config_route()
        self.configer.config_patch()
        self.configer.config_storge()
        #self.configer.config_extnet()

    def unregister_cloud(self):
        self.configer.remove_existed_cloud()


class AddServie(object):
    def __init__(self):
        pass

    def deploy_service(self):
        pass

    def delete_service(self):
        pass

    def config_service(self):
        pass








