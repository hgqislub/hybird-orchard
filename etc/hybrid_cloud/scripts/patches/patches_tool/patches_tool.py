__author__ = 'nash.xiejun'
import log
import os
import stat
import time

import config
import utils
from constants import PatchFilePath
from dispatch import DispatchPatchTool
from services import RefCPSService, CPSServiceBusiness
from utils import SSHConnection

logger = log
print_logger = log


class InstallerBase(object):
    def install(self):
        return True


class PatchInstaller(InstallerBase):

    def __init__(self, patch_path, openstack_install_path, filters, host):
        """

        :param patch_path:
            for example: /root/tricircle-master/novaproxy/
                        /root/tricircle-master/juno-patches/nova_scheduling_patch/
        :param openstack_install_path:
            for example: '/usr/lib/python2.7/dist-packages/'
        :param filters:
            for example: ['.py']
        :return:
        """
        self.patch_path = patch_path
        self.host_ip = host
        self.openstack_install_path = openstack_install_path
        self.filters = filters

    def get_patch_files(self, patch_path, filters):
        """

        :param patch_path: path of patch's source code
        :param filters: [] array of valid suffix of file. for example: ['.py']
        :return: (absolute path, relative path)
            for example:
            [(/root/tricircle-master/novaproxy/nova/compute/clients.py,
            nova/compute/clients.py), ..]
        """
        return utils.get_files(patch_path, filters)

    def install(self):
        result = 'FAILED'
        patch_files = self.get_patch_files(self.patch_path, self.filters)
        if not patch_files:
            logger.error('No files in %s' % self.patch_path)
        for absolute_path, relative_path in patch_files:
            # installed_path is full install path,
            openstack_installed_file = os.path.join(self.openstack_install_path, relative_path)

            copy_dir = os.path.dirname(openstack_installed_file)

            ssh = SSHConnection(self.host_ip, 'root', 'Huawei@CLOUD8!')
            try:
                if not stat.S_ISDIR(ssh.get_sftp().stat(copy_dir).st_mode):
                    log.info('create dir: %s' % copy_dir)
                    ssh.get_sftp().mkdir(copy_dir)
                ssh.put(absolute_path, openstack_installed_file)
            except IOError, e:
                if e.args[1] == 'No such file':
                    log.info('There is no such dir in host: %s, create dir: %s' % (self.host_ip, copy_dir))
                    cmd = "mkdir -p %s" % copy_dir
                    utils.remote_execute_cmd(host_ip=self.host_ip, user="root", passwd="Huawei@CLOUD8!", cmd=cmd)
                else:
                     error_message = 'Exception occure when copy file<%s>, Exception.args: %s' \
                                % (openstack_installed_file, e.args)
                     log.error(error_message)
                     print(error_message)
            except Exception, e:
                error_message = 'Exception occure when copy file<%s>, Exception.args: %s' \
                                % (openstack_installed_file, e.args)
                log.error(error_message)
                print(error_message)

            finally:
                ssh.close()

        result = 'SUCCESS'
        return result

class PatchesTool(object):

    def __init__(self):
        self.proxy_match_region = config.CONF.DEFAULT.proxy_match_region

    def patch_for_cascading_and_proxy_node(self):
        host_list = RefCPSService.host_list()
        for host in host_list['hosts']:
            roles_list = host['roles']
            proxy_host_ip = host['manageip']
            region = self._get_region_by_roles_list(roles_list)
            if region is not None:
                print('Start to patch for region - <%s>' % region)
                absolute_patch_path = self._get_path_by_region(region)
                PatchInstaller(absolute_patch_path, utils.get_openstack_installed_path(), ['.py'], proxy_host_ip).install()
                print('Finish to patch for region - <%s>' % region)
            else:
                print('Region of ip <%s> is None, can not patch for this proxy' % proxy_host_ip)

    def patch_for_cascaded_nodes(self):
        cps = CPSServiceBusiness()


    def _get_path_by_region(self, region):
        absolute_cascading_patch_path = os.path.sep.join([
                                                             utils.get_patches_tool_path(), PatchFilePath.PATCH_FOR_CASCADING])
        absolute_aws_proxy_patch_path = os.path.sep.join([
                                                             utils.get_patches_tool_path(), PatchFilePath.PATCH_FOR_AWS_PROXY])
        absolute_vcloud_proxy_patch_path = os.path.sep.join([
                                                                utils.get_patches_tool_path(), PatchFilePath.PATCH_FOR_VCLOUD_PROXY])

        if 'aws' in region:
            return absolute_aws_proxy_patch_path
        elif 'vcloud' in region:
            return absolute_vcloud_proxy_patch_path
        else:
            return absolute_cascading_patch_path

    def _get_region_by_roles_list(self, roles_list):
        for role in roles_list:
            if 'compute-proxy' in role:
                proxy_number = role.split('-')[1]
                print("proxy_number = %s" % proxy_number)
                print("self.proxy_match_region = %s" % self.proxy_match_region)
                try:
                    return self.proxy_match_region[proxy_number]
                except Exception as e:
                    return None
        return None

    def restart_service(self):
        log.info('Start to restart openstack service for nova/neutron/cinder.')
        cps_service = CPSServiceBusiness()
        for proxy in self.proxy_match_region.keys():
            cps_service.stop_all(proxy)
            cps_service.start_all(proxy)
        log.info('Finish to restart openstack service for nova/neutron/cinder.')


    def verify_services_status(self):
        cps_service = CPSServiceBusiness()
        for proxy in self.proxy_match_region.keys():
            cps_service.check_all_service_template_status(proxy)

if __name__ == '__main__':
    log.init('patches_tool_config')
    config.export_env()

    print('Start to patch Hybrid-Cloud patches in cascading node and proxy nodes...')
    log.info('Start to patch Hybrid-Cloud patches in cascading node and proxy nodes...')

    patches_tool = PatchesTool()
    patches_tool.patch_for_cascading_and_proxy_node()

    print('Finish to patch Hybrid-Cloud patches in cascading node and proxy nodes...')
    log.info('Finish to patch Hybrid-Cloud patches in cascading node and proxy nodes...')

    print('Start to patch Hybrid-Cloud patches in cascaded nodes...')
    log.info('Start to patch Hybrid-Cloud patches in cascaded nodes...')

    dispatch_patch_tool = DispatchPatchTool(proxy_match_region=config.CONF.DEFAULT.proxy_match_region)
    dispatch_patch_tool.remote_patch_for_cascaded_nodes()

    print('Finish to patch Hybrid-Cloud patches in cascaded nodes...')
    log.info('Finish to patch Hybrid-Cloud patches in cascaded nodes...')

    print('Start to restart openstack service for nova/neutron/cinder.')
    patches_tool.restart_service()
    print('Finish to restart openstack service for nova/neutron/cinder.')

    print('Start to verify services status')
    time.sleep(5)
    patches_tool.verify_services_status()
    print('Finish to verify services status')

    print('**** If found some status of some services are fault, ****')
    print('**** Please check it after more then 10 seconds, it is because the service is restarting... ###')
    print('*** To check by using this commands: # python config.py check')

    print('Finish to patch Hybrid-Cloud patches in cascaded nodes...')


