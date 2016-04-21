import pdb

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))

import time
import socket
from heat.openstack.common import log as logging
import cloud_util as utils
from cloudmanager.exception import *
from cloudmanager.environmentinfo import *
import vcloud_proxy_install as proxy_installer
import vcloud_cloudinfo as data_handler
import json
from cloudmanager.subnet_manager import SubnetManager
from vcloudcloudpersist import VcloudCloudDataHandler


LOG = logging.getLogger(__name__)

_install_conf = os.path.join("/home/hybrid_cloud/conf/vcloud",
                             'vcloud_access_cloud_install.conf')


def _read_install_conf():
    if not os.path.exists(_install_conf):
        LOG.error("read %s : No such file." % _install_conf)
        return None
    with open(_install_conf, 'r+') as fd:
        tmp = fd.read()
        return json.loads(tmp)


def _write_install_conf():
    #TODO(lrx):modify to vcloud
    install_conf = {"cascaded_image": "OpenStack-AZ11",
                    "vpn_image": "local-vpn-template-qf" }

    with open(_install_conf, 'w+') as fd:
        fd.write(json.dumps(install_conf, indent=4))
        return install_conf

def distribute_subnet():

        cloud_subnet = SubnetManager().distribute_subnet_pair()
        cloud_subnet["hynode_control"] = "172.29.251.0/24"
        cloud_subnet["hynode_data"] = "172.29.252.0/24"
        return cloud_subnet



class HwscloudInstaller(utils.CloudUtil):
    def __init__(self,cloud_id=None,
                       cloud_params=None, vcloud_url=None,
                       vcloud_org=None,
                       vcloud_vdc=None,
                       vcloud_edgegw=None,
                       username=None,
                       passwd=None,
                       region=None):
        self.cloud_id= cloud_id
        self.vcloud_url = vcloud_url
        self.vcloud_org = vcloud_org
        self.vcloud_vdc = vcloud_vdc
        self.vcloud_edgegw = vcloud_edgegw
        self.username = username
        self.passwd = passwd
        self.region = region
        self.cloud_type = None

        self.init_params(cloud_params)

        self._read_env()
        cloud_subnet = distribute_subnet()

        self.api_cidr=cloud_subnet["cloud_api"]
        self.tunnel_cidr=cloud_subnet["cloud_tunnel"]

        self.local_api_cidr=self.local_api_subnet
        self.local_tunnel_cidr=self.local_tunnel_subnet

        self.debug_cidr = None
        self.base_cidr = None




        if self.local_vpn_public_gw == self.cascading_eip:
            self.green_ips = [self.local_vpn_public_gw]
        else:
            self.green_ips = [self.local_vpn_public_gw, self.cascading_eip]


        self.installer = vcloudair.VCA(host=self.vcloud_url, username=self.username, service_type='vcd',
                                       version='5.5', verify=False)

        install_conf = _read_install_conf()
        #install_conf = {}

        self.cascaded_image = install_conf["cascaded_image"]

        self.vpn_image = install_conf["vpn_image"]


        #vdc network
        self.api_gw=None,
        self.api_subnet_cidr=None
        self.tunnel_gw=None
        self.tunnel_subnet_cidr=None

        #cascaded
        self.public_ip_api_reverse = None
        self.public_ip_api_forward = None
        self.public_ip_ntp_server = None
        self.public_ip_ntp_client = None
        self.public_ip_cps_web = None


        self.cascaded_base_ip=None
        self.cascaded_api_ip=None
        self.cascaded_tunnel_ip=None

        #vpn

        self.public_ip_vpn = None
        self.vpn_api_ip = None
        self.vpn_tunnel_ip = None


        self.ext_net_eips = {}

        self.all_public_ip = []
        self.free_public_ip = []

        self._read_vcloud_access_cloud()

    def init_params(self,cloud_params):
        if cloud_params == None:
            return
        self.region = cloud_params['region_name']
        self.azname = cloud_params['azname']
        self.availabilityzone = cloud_params['availabilityzone']
        self.vcloud_url = cloud_params['vcloud_url']
        self.vcloud_org = cloud_params['vcloud_org']
        self.vcloud_vdc = cloud_params['vcloud_vdc']
        self.vcloud_edgegw = cloud_params['vcloud_edgegw']
        self.username = cloud_params['username']
        self.passwd = cloud_params['passwd']
        self.access = cloud_params['access']
        self.cloud_type = cloud_params['cloud_type']

        self.cloud_id = "@".join([cloud_params['vcloud_url'],cloud_params['vcloud_org'],
                                  cloud_params['vcloud_vdc'], cloud_params['region_name'],
                                  cloud_params['azname']])

    def _read_env(self):
        try:
            env_info = read_environment_info(self.cloud_type)
            self.env = env_info["env"]
            self.cascading_api_ip = env_info["cascading_api_ip"]
            self.cascading_domain = env_info["cascading_domain"]
            self.local_vpn_ip = env_info["local_vpn_ip"]
            self.local_vpn_public_gw = env_info["local_vpn_public_gw"]
            self.cascading_eip = env_info["cascading_eip"]
            self.local_api_subnet = env_info["local_api_subnet"]
            self.local_vpn_api_ip = env_info["local_vpn_api_ip"]
            self.local_tunnel_subnet = env_info["local_tunnel_subnet"]
            self.local_vpn_tunnel_ip = env_info["local_vpn_tunnel_ip"]
            self.existed_cascaded = env_info["existed_cascaded"]
        except ReadEnvironmentInfoFailure as e:
            LOG.error(
                "read environment info error. check the config file: %s"
                % e.message)
            raise ReadEnvironmentInfoFailure(error=e.message)

    def _distribute_cloud_domain(self, region_name, azname, az_tag):
        """distribute cloud domain
        :return:
        """
        domain_list = self.cascading_domain.split(".")
        domainpostfix = ".".join([domain_list[2], domain_list[3]])
        l_region_name = region_name.lower()
        cloud_cascaded_domain = ".".join(
                [azname, l_region_name + az_tag, domainpostfix])
        return cloud_cascaded_domain

    def _domain_to_region(domain):
        domain_list = domain.split(".")
        region = domain_list[0] + "." + domain_list[1]
        return region

    def _read_vcloud_access_cloud(self):
        cloud_info = data_handler.get_vcloud_access_cloud(self.cloud_id)
        if not cloud_info:
            return

        if "vdc_network" in cloud_info.keys():
            vdc_network_info = cloud_info["vdc_network"]

            self.api_gw=vdc_network_info["api_gw"],
            self.api_subnet_cidr=vdc_network_info["api_subnet_cidr"]
            self.tunnel_gw=vdc_network_info["tunnel_gw"]
            self.tunnel_subnet_cidr=vdc_network_info["tunnel_subnet_cidr"]


        if "cascaded" in cloud_info.keys():
            cascaded_info = cloud_info["cascaded"]
            self.public_ip_api_reverse = cascaded_info["public_ip_api_reverse"]
            self.public_ip_api_forward = cascaded_info["public_ip_api_forward"]
            self.public_ip_ntp_server = cascaded_info["public_ip_ntp_server"]
            self.public_ip_ntp_client = cascaded_info["public_ip_ntp_client"]
            self.public_ip_cps_web = cascaded_info["public_ip_cps_web"]


            self.cascaded_base_ip= cascaded_info["cascaded_base_ip"]
            self.cascaded_api_ip= cascaded_info["cascaded_api_ip"]
            self.cascaded_tunnel_ip= cascaded_info["cascaded_tunnel_ip"]

        if "vpn" in cloud_info.keys():
            vpn_info = cloud_info["vpn"]
            self.public_ip_vpn = vpn_info["public_ip_vpn"]
            self.vpn_api_ip =  vpn_info["vpn_api_ip"]
            self.vpn_tunnel_ip =  vpn_info["vpn_tunnel_ip"]


        if "ext_net_eips" in cloud_info.keys():
            self.ext_net_eips = cloud_info["ext_net_eips"]

    def create_vm(self, vapp_name, template_name, catalog_name):
        #pdb.set_trace()
        result = self.installer.create_vapp(self.vcloud_vdc, vapp_name=vapp_name,
                         template_name=template_name,
                         catalog_name=catalog_name,
                         network_name=None,
                         network_mode='bridged',
                         vm_name=None,
                         vm_cpus=None,
                         vm_memory=None,
                         deploy='false',
                         poweron='false')
        if result == False:
            LOG.error('create vm faild vapp=%s. vdc=%s' %(vapp_name,self.vcloud_vdc))
            return False
        else:
            self.installer.block_until_completed(result)
            return True


    def delete_vm(self, vapp_name):
        result = self.installer.delete_vapp(vdc_name=self.vcloud_vdc,vapp_name=vapp_name)
        if result == False:
            LOG.error('delete vm faild vapp=%s. vdc=%s' %(vapp_name,self.vcloud_vdc))
            return False
        else:
            self.installer.block_until_completed(result)
            return True

    def create_network(self):
        pass

    def delete_network(self):
        pass

    def install_proxy(self):
        return proxy_installer.install_vcloud_proxy()

    def cloud_preinstall(self):
        self.installer_login()
        network_num = []
        #pdb.set_trace()
        while(len(network_num) < 3 ):
            self.install_network()
            network_num = self.installer.get_networks(vdc_name=self.vcloud_vdc)
        #pdb.set_trace()
        self.set_free_public_ip()
        self.installer_logout()


    def set_free_public_ip(self):
        if len(self.all_public_ip) == 0 :
            the_gw = self.installer.get_gateway(vdc_name=self.vcloud_vdc,gateway_name=self.vcloud_edgegw)
            self.all_public_ip = sorted(the_gw.get_public_ips(), key=socket.inet_aton)
            all_public_ip_temp = sorted(the_gw.get_public_ips(), key=socket.inet_aton)
            #delete edge ip
            del self.all_public_ip[0]
            del all_public_ip_temp[0]

        #get 10 free public ip from all public ip
        count = 0
        for ip in all_public_ip_temp:
            data = os.system("ping -c 1 %s > /dev/null 2>&1" % ip)
            if data!=0:
                self.free_public_ip.append(ip)
                self.all_public_ip.remove(ip)
                count += 1
            if count > 10:
                break

        if len(self.free_public_ip) == 0:
            LOG.error('set free public ip failed, no free ip can be allocate')


    def get_free_public_ip(self):
        free_ip = self.free_public_ip[0]
        if len(self.free_public_ip) > 0:
            self.free_public_ip.remove(free_ip)
            return free_ip
        else :
            LOG.error('get free public ip failed, no free ip remain')
            return None


    def installer_login(self):
        self.installer.login(password=self.passwd,org=self.vcloud_org)
        self.installer.login(token=self.installer.token, org=self.vcloud_org,
                             org_url=self.installer.vcloud_session.org_url)

    def installer_logout(self):
        self.installer.logout()

    def install_network(self):
        #create vcloud network
        #create base net
        #pdb.set_trace()
        result = self.installer.create_vdc_network(self.vcloud_vdc,network_name='base_net',
                                    gateway_name=self.vcloud_edgegw,
                                    start_address='172.28.0.2',
                                    end_address='172.28.0.100',
                                    gateway_ip='172.28.0.1',
                                    netmask='255.255.240.0',
                                    dns1=None,
                                    dns2=None,
                                    dns_suffix=None)
        if result[0] == False:
            LOG.error('create vcloud base net failed at vdc=%s.' %self.vcloud_vdc)
        else :
            self.installer.block_until_completed(result[1])


        #create data net
        self.installer.create_vdc_network(self.vcloud_vdc,network_name='data_net',
                                    gateway_name=self.vcloud_edgegw,
                                    start_address='172.30.16.2',
                                    end_address='172.30.16.100',
                                    gateway_ip='172.30.16.1',
                                    netmask='255.255.240.0',
                                    dns1=None,
                                    dns2=None,
                                    dns_suffix=None)
        if result[0] == False:
            LOG.error('create vcloud data net failed at vdc=%s.' %self.vcloud_vdc)
        else :
            self.installer.block_until_completed(result[1])


        #create ext net
        self.installer.create_vdc_network(self.vcloud_vdc,network_name='ext_net',
                                    gateway_name=self.vcloud_edgegw,
                                    start_address='172.30.0.2',
                                    end_address='172.30.0.100',
                                    gateway_ip='172.30.0.1',
                                    netmask='255.255.240.0',
                                    dns1=None,
                                    dns2=None,
                                    dns_suffix=None)
        if result[0] == False:
            LOG.error('create vcloud base net failed at vdc=%s.' %self.vcloud_vdc)
        else :
            self.installer.block_until_completed(result[1])



        network_num = self.installer.get_networks(vdc_name=self.vcloud_vdc)
        if len(network_num) == 3:
            LOG.info('create vcloud vdc network success.')
            self.api_gw='172.30.0.1',
            self.api_subnet_cidr='172.30.0.0/20',
            self.tunnel_gw='172.30.16.1',
            self.tunnel_subnet_cidr='172.30.16.0/20'
            data_handler.write_vdc_network(self.cloud_id,
                                          self.api_gw,
                                          self.api_subnet_cidr,
                                          self.tunnel_gw,
                                          self.tunnel_subnet_cidr
                                          )
        else :
            LOG.info('one or more vcloud vdc network create failed.')


    def uninstall_network(self):
        #delete all vdc network
        result = self.installer.delete_vdc_network(self.vcloud_vdc,network_name='base_net')
        if result[0] == False:
            LOG.error('delete vcloud base net failed at vdc=%s.' %self.vcloud_vdc)
        else :
            self.installer.block_until_completed(result[1])

        result = self.installer.delete_vdc_network(self.vcloud_vdc,network_name='data_net')
        if result[0] == False:
            LOG.error('delete vcloud base net failed at vdc=%s.' %self.vcloud_vdc)
        else :
            self.installer.block_until_completed(result[1])

        result = self.installer.delete_vdc_network(self.vcloud_vdc,network_name='ext_net')
        if result[0] == False:
            LOG.error('delete vcloud base net failed at vdc=%s.' %self.vcloud_vdc)
        else :
            self.installer.block_until_completed(result[1])

        network_num = self.installer.get_networks(vdc_name=self.vcloud_vdc)
        if len(network_num) == 0:
            LOG.info('delete all vcloud vdc network success.')


    def create_vapp_network(self, network_name,vapp_name):
        the_vdc=self.installer.get_vdc(self.vcloud_vdc)
        the_vapp=self.installer.get_vapp(the_vdc, vapp_name=vapp_name)
        nets = filter(lambda n: n.name == network_name, self.installer.get_networks(self.vcloud_vdc))
        task = the_vapp.connect_to_network(nets[0].name, nets[0].href)
        result = self.installer.block_until_completed(task)

        if result == False:
            LOG.error('create vapp network failed network=%s vapp=%s.' %(network_name, the_vapp.name))

    def connect_vms_to_vapp_network(self, network_name, vapp_name, nic_index=0, primary_index=0,
                                    mode='DHCP', ipaddr=None):
        #pdb.set_trace()
        the_vdc=self.installer.get_vdc(self.vcloud_vdc)
        the_vapp=self.installer.get_vapp(the_vdc, vapp_name=vapp_name)
        nets = filter(lambda n: n.name == network_name, self.installer.get_networks(self.vcloud_vdc))
        task = the_vapp.connect_vms(network_name=nets[0].name,
                                connection_index=nic_index,
                                connections_primary_index=primary_index,
                                ip_allocation_mode=mode.upper(),
                                mac_address=None,
                                ip_address=ipaddr)
        result = self.installer.block_until_completed(task)

        if result == False:
            LOG.error('connect vms to vapp network failed network=%s vapp=%s.' %(network_name, vapp_name))


    def add_nat_rule(self, original_ip, translated_ip):
        #TODO(lrx):how to get gateway_name
        #pdb.set_trace()
        the_gw=self.installer.get_gateway(vdc_name=self.vcloud_vdc,gateway_name=self.vcloud_edgegw)
        the_gw.add_nat_rule(rule_type='DNAT',
               original_ip=original_ip,
               original_port='any',
               translated_ip=translated_ip,
               translated_port='any',
               protocol='any'
               )
        the_gw.add_nat_rule(rule_type='SNAT',
               original_ip=translated_ip,
               original_port='any',
               translated_ip=original_ip,
               translated_port='any',
               protocol='any'
               )

        task = the_gw.save_services_configuration()
        result = self.installer.block_until_completed(task)
        if result == False:
            LOG.error('add nat rule failed vdc=%s .' %(self.vcloud_vdc))
        else :
            LOG.info('add nat rule success vdc=%s .' %(self.vcloud_vdc))

    def delete_nat_rule(self, original_ip, translated_ip):
        #TODO(lrx):how to get gateway_name
        #pdb.set_trace()
        the_gw=self.installer.get_gateway(vdc_name=self.vcloud_vdc,gateway_name=self.vcloud_edgegw)
        the_gw.del_nat_rule(rule_type='DNAT',
               original_ip=original_ip,
               original_port='any',
               translated_ip=translated_ip,
               translated_port='any',
               protocol='any'
               )
        the_gw.del_nat_rule(rule_type='SNAT',
               original_ip=translated_ip,
               original_port='any',
               translated_ip=original_ip,
               translated_port='any',
               protocol='any'
               )

        task = the_gw.save_services_configuration()
        result = self.installer.block_until_completed(task)
        if result == False:
            LOG.error('delete nat rule failed vdc=%s .' %(self.vcloud_vdc))
        else :
            LOG.info('delete nat rule success vdc=%s .' %(self.vcloud_vdc))


    def add_dhcp_pool(self):
        the_gw=self.installer.get_gateway(vdc_name=self.vcloud_vdc,gateway_name=self.vcloud_edgegw)
        the_gw.add_dhcp_pool(network_name='data_net',
                                      low_ip_address='172.30.16.101',
                                      hight_ip_address='172.30.18.100',
                                      default_lease=3600,
                                      max_lease=7200)
        the_gw.add_dhcp_pool(network_name='base_net',
                                      low_ip_address='172.28.0.101',
                                      hight_ip_address='172.28.2.100',
                                      default_lease=3600,
                                      max_lease=7200)

        task = the_gw.save_services_configuration()
        result = self.installer.block_until_completed(task)
        if result == False:
            LOG.error('add dhcp failed vdc=%s .' %(self.vcloud_vdc))
        else :
            LOG.info('add dhcp success vdc=%s .' %(self.vcloud_vdc))

    def delete_dhcp_pool(self):
        the_gw=self.installer.get_gateway(vdc_name=self.vcloud_vdc,gateway_name=self.vcloud_edgegw)
        the_gw.delete_dhcp_pool(network_name='data_net')
        the_gw.delete_dhcp_pool(network_name='base_net')

        task = the_gw.save_services_configuration()
        result = self.installer.block_until_completed(task)
        if result == False:
            LOG.error('delete dhcp failed vdc=%s .' %(self.vcloud_vdc))
        else :
            LOG.info('delete dhcp success vdc=%s .' %(self.vcloud_vdc))

    def vapp_deploy(self,vapp_name):
        the_vdc=self.installer.get_vdc(self.vcloud_vdc)
        the_vapp=self.installer.get_vapp(the_vdc, vapp_name=vapp_name)
        task=the_vapp.deploy(powerOn='True')
        result = self.installer.block_until_completed(task)
        if result == False:
            LOG.error('power on vapp=%s failed vdc=%s .' %(vapp_name,self.vcloud_vdc))
        else :
            LOG.info('power on vapp=%s success vdc=%s .' %(vapp_name,self.vcloud_vdc))
        time.sleep(20)

    def vapp_undeploy(self,vapp_name):
        the_vdc=self.installer.get_vdc(self.vcloud_vdc)
        the_vapp=self.installer.get_vapp(the_vdc, vapp_name=vapp_name)
        task=the_vapp.undeploy(action='powerOff')
        result = self.installer.block_until_completed(task)
        if result == False:
            LOG.error('shutdown  vapp=%s failed vdc=%s .' %(vapp_name,self.vcloud_vdc))
        else :
            LOG.info('shutdown  vapp=%s success vdc=%s .' %(vapp_name,self.vcloud_vdc))
        time.sleep(20)


    def cloud_postinstall(self, cloudinfo):
        VcloudCloudDataHandler().add_vcloud_cloud(cloudinfo)

    def cloud_postuninstall(self):
        #delete vdc network
        self.installer_login()
        network_num = self.installer.get_networks(vdc_name=self.vcloud_vdc)
        #pdb.set_trace()
        while(len(network_num) > 0 ):
            self.uninstall_network()
            network_num = self.installer.get_networks(vdc_name=self.vcloud_vdc)
        self.installer_logout()

    def install_cascaded(self):
         #pdb.set_trace()
         self._install_cascaded()

    def _install_cascaded(self):
        #TODO(lrx):how to get vapp name
        #pdb.set_trace()
        self.installer_login()
        cascaded_image = self.cascaded_image
        result = self.create_vm(vapp_name=cascaded_image,
                                          template_name=cascaded_image,
                                          catalog_name='vapptemplate')
        if result == False :
            return
        else :
            #create vapp network
            self.create_vapp_network(network_name='base_net', vapp_name=cascaded_image)
            self.create_vapp_network(network_name='ext_net', vapp_name=cascaded_image)
            self.create_vapp_network(network_name='data_net', vapp_name=cascaded_image)
            time.sleep(10)

            #connect vms to vapp network
            self.cascaded_base_ip='172.28.0.70'
            self.cascaded_api_ip='172.30.0.70'
            self.cascaded_tunnel_ip='172.30.16.70'
            self.connect_vms_to_vapp_network(network_name='base_net', vapp_name=cascaded_image, nic_index=0, primary_index=0,
                                             mode='MANUAL', ipaddr=self.cascaded_base_ip)
            self.connect_vms_to_vapp_network(network_name='ext_net', vapp_name=cascaded_image, nic_index=1, primary_index=None,
                                             mode='MANUAL', ipaddr=self.cascaded_api_ip)
            self.connect_vms_to_vapp_network(network_name='data_net', vapp_name=cascaded_image, nic_index=2, primary_index=None,
                                             mode='MANUAL', ipaddr=self.cascaded_tunnel_ip)

        #add NAT rule to connect ext net
        self.public_ip_api_reverse = self.get_free_public_ip()
        self.public_ip_api_forward = self.get_free_public_ip()
        self.public_ip_ntp_server = self.get_free_public_ip()
        self.public_ip_ntp_client = self.get_free_public_ip()
        self.public_ip_cps_web = self.get_free_public_ip()
        self.add_nat_rule(original_ip=self.public_ip_api_reverse, translated_ip='172.30.0.70')
        self.add_nat_rule(original_ip=self.public_ip_api_forward, translated_ip='172.30.0.71')
        self.add_nat_rule(original_ip=self.public_ip_ntp_server, translated_ip='172.30.0.72')
        self.add_nat_rule(original_ip=self.public_ip_ntp_client, translated_ip='172.30.0.73')
        self.add_nat_rule(original_ip=self.public_ip_cps_web, translated_ip='172.28.11.42')


        #add dhcp pool
        self.add_dhcp_pool()
        #pdb.set_trace()
        #poweron the vapp
        self.vapp_deploy(vapp_name=cascaded_image)


        self.installer_logout()

        data_handler.write_cascaded(self.cloud_id,
                                    self.public_ip_api_reverse,
                                    self.public_ip_api_forward,
                                    self.public_ip_ntp_server,
                                    self.public_ip_ntp_client,
                                    self.public_ip_cps_web,
                                    self.cascaded_base_ip,
                                    self.cascaded_api_ip,
                                    self.cascaded_tunnel_ip)

        LOG.info("install cascaded success.")


    def uninstall_cascaded(self):
        self._uninstall_cascaded()

    def _uninstall_cascaded(self):
        self.installer_login()
        cascaded_image = self.cascaded_image

        #power off vapp
        self.vapp_undeploy(vapp_name=cascaded_image)

        #delete nat rules and dhcp pool
        self.delete_nat_rule(original_ip=self.public_ip_api_reverse, translated_ip='172.30.0.70')
        self.delete_nat_rule(original_ip=self.public_ip_api_forward, translated_ip='172.30.0.71')
        self.delete_nat_rule(original_ip=self.public_ip_ntp_server, translated_ip='172.30.0.72')
        self.delete_nat_rule(original_ip=self.public_ip_ntp_client, translated_ip='172.30.0.73')
        self.delete_nat_rule(original_ip=self.public_ip_cps_web, translated_ip='172.28.11.42')

        self.delete_dhcp_pool()

        #delete vapp

        result = self.delete_vm(vapp_name=cascaded_image)
        self.installer_logout()
        if result == False :
            return
        else:
            LOG.info("uninstall cascaded success.")

    def install_vpn(self):
        self._install_vpn()

    def _install_vpn(self):
        self.installer_login()
        #pdb.set_trace()
        vpn_image = self.vpn_image
        result = self.create_vm(vapp_name=vpn_image,
                                          template_name=vpn_image,
                                          catalog_name='vapptemplate')


        if result == False :
            return
        else :
            #create vapp network
            self.create_vapp_network(network_name='ext_net', vapp_name=vpn_image)
            self.create_vapp_network(network_name='data_net', vapp_name=vpn_image)
            time.sleep(10)

            #connect vms to vapp network
            self.connect_vms_to_vapp_network(network_name='ext_net', vapp_name=vpn_image, nic_index=0, primary_index=None,
                                             mode='POOL', ipaddr=None)
            self.connect_vms_to_vapp_network(network_name='data_net', vapp_name=vpn_image, nic_index=1, primary_index=None,
                                             mode='POOL', ipaddr=None)

        #add NAT rule to connect ext net
        self.public_ip_vpn = self.get_free_public_ip()
        self.add_nat_rule(original_ip=self.public_ip_vpn, translated_ip='172.30.0.254')

        #poweron the vapp
        self.vapp_deploy(vapp_name=vpn_image)

        self.installer.logout()
        self.vpn_api_ip = '172.30.0.254'
        self.vpn_tunnel_ip='172.30.31.254'
        data_handler.write_vpn(self.cloud_id,
                               self.public_ip_vpn,
                               self.vpn_api_ip,
                               self.vpn_tunnel_ip)

    def uninstall_vpn(self):
        self._uninstall_vpn()

    def _uninstall_vpn(self):
        self.installer_login()
        vpn_image = self.vpn_image

        #power off vapp
        self.vapp_undeploy(vapp_name=vpn_image)

        #delete nat rules
        self.delete_nat_rule(original_ip=self.public_ip_vpn, translated_ip='172.30.0.254')

        #delete vapp

        result = self.delete_vm(vapp_name=vpn_image)
        self.installer_logout()
        if result == False :
            return
        else:
            LOG.info("uninstall vpn success.")


    def package_installinfo(self):
        return self.package_vcloud_access_cloud_info()

    def package_vcloud_access_cloud_info(self):
        #TODO(lrx):modify the info params
        info = {"vdc_network":
                    {"api_gw": self.api_gw,
                    "api_subnet_cidr": self.api_subnet_cidr,
                    "tunnel_gw": self.tunnel_gw,
                    "tunnel_subnet_cidr": self.tunnel_subnet_cidr
                     },
                "cascaded":
                    {"public_ip_api_reverse": self.public_ip_api_reverse,
                     "public_ip_api_forward": self.public_ip_api_forward,
                     "public_ip_ntp_server": self.public_ip_ntp_server,
                     "public_ip_ntp_client": self.public_ip_ntp_client,
                     "public_ip_cps_web": self.public_ip_cps_web,
                     "base_ip": self.cascaded_base_ip,
                     "api_ip": self.cascaded_api_ip,
                     "tunnel_ip": self.cascaded_tunnel_ip},
                "vpn":
                    {
                     "public_ip_vpn":self.public_ip_vpn,
                     "vpn_api_ip":self.vpn_api_ip,
                     "vpn_tunnel_ip":self.vpn_tunnel_ip},

                "ext_net_eips": self.ext_net_eips.keys()}
        return info

    def get_vcloud_access_cloud_install_info(self,installer):
                return installer.package_vcloud_access_cloud_info()






