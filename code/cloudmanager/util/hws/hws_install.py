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
from conf_util import *
from hws_util import *


LOG = logging.getLogger(__name__)

_environment_conf = os.path.join("/home/hybrid_cloud/conf/hws/",
                             'environment.conf')
_install_conf = os.path.join("/home/hybrid_cloud/conf/hws/",
                             'hws_access_cloud_install.conf')
_vpc_conf = os.path.join("/home/hybrid_cloud/conf/hws/",
                             'hws_vpc.conf')
SUBNET_GATEWAY_TAIL_IP = "1"
HTTP_OK = "200"

class HwsCascadedInstaller(utils.CloudUtil):
    def __init__(self, cloud_params):
        self._init_params(cloud_params)
        self._read_env()
        self._read_install_conf()


    def _init_params(self, cloud_params):
        self.cloud_info = cloud_params
        self.cloud_id = "@".join([cloud_params['project_id'], cloud_params['azname']])
        self.installer = HwsInstaller(cloud_params)

    def _read_env(self):
        try:
            env_info = read_conf(_environment_conf)
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
        except IOError as e:
            error = "read file = ".join([_install_conf, " error"])
            LOG.error(e)
            raise ReadEnvironmentInfoFailure(error = error)
        except KeyError as e:
            error = "read key = ".join([e.message, " error in file = ", _install_conf])
            LOG.error(error)
            raise ReadEnvironmentInfoFailure(error = error)

    def _read_install_conf(self):
        try:
            install_info = read_conf(_install_conf)
            self.cascaded_image = install_info["cascaded_image"]
            self.cascaded_flavor = install_info["cascaded_flavor"]
            self.vpn_image = install_info["vpn_image"]
            self.vpn_flavor = install_info["vpn_flavor"]

        except IOError as e:
            error = "read file = ".join([_install_conf, " error"])
            LOG.error(e)
            raise ReadEnvironmentInfoFailure(error = error)
        except KeyError as e:
            error = "read key = ".join([e.message, " error in file = ", _install_conf])
            LOG.error(error)
            raise ReadEnvironmentInfoFailure(error = error)

    def _read_vpc_conf(self):
        try:
            vpc_conf = read_conf(_vpc_conf)
            self.vpc_info = vpc_conf["vpc_info"]
            self.external_api_info = vpc_conf["external_api_info"]
            self.tunnel_bearing_info = vpc_conf["tunnel_bearing_info"]
            self.internal_base_info = vpc_conf["internal_base_info"]
            self.debug_info = vpc_conf["debug_info"]

        except IOError as e:
            error = "read file = ".join([_install_conf, " error"])
            LOG.error(e)
            raise ReadEnvironmentInfoFailure(error = error)
        except KeyError as e:
            error = "read key = ".join([e.message, " error in file = ", _install_conf])
            LOG.error(error)
            raise ReadEnvironmentInfoFailure(error = error)

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

    def _create_vpc(self):
        name = self.vpc_info["name"]
        cidr = self.vpc_info["cidr"]
        self.vpc_id = self.installer.create_vpc(name, cidr)

    def _delete_vpc(self):
        self.installer.delete_vpc(self.vpc_id)

    def _create_subnet(self):
        az = self.cloud_info["availability_zone"]
        external_api_cidr = self.external_api_info["cidr"]
        external_api_gateway = self._get_gateway_ip(external_api_cidr)
        tunnel_bearing_cidr = self.tunnel_bearing_info["cidr"]
        tunnel_bearing_gateway = self._get_gateway_ip(tunnel_bearing_cidr)
        internal_base_cidr = self.internal_base_info["cidr"]
        internal_base_gateway = self._get_gateway_ip(internal_base_cidr)
        debug_cidr = self.debug_info["cidr"]
        debug_gateway = self._get_gateway_ip(debug_cidr)

        self.external_api_id = self.installer.create_subnet("external_api",
                                external_api_cidr, external_api_gateway,
                                az, self.vpc_id)
        self.tunnel_bearing_id = self.installer.create_subnet("tunnel_bearing",
                              tunnel_bearing_cidr, tunnel_bearing_gateway,
                              az, self.vpc_id)
        self.internal_base_id = self.installer.create_subnet("internal_base",
                              internal_base_cidr, internal_base_gateway,
                              az, self.vpc_id)
        self.debug_id = self.installer.create_subnet("debug",
                              debug_cidr, debug_gateway,
                              az, self.vpc_id)

    def _delete_subnet(self):
        self.installer.delete_subnet(self.external_api_id)
        self.installer.delete_subnet(self.tunnel_bearing_id)
        self.installer.delete_subnet(self.internal_base_id)
        self.installer.delete_subnet(self.debug_id)

    @staticmethod
    def _get_gateway_ip(cidr):
        ip_list = cidr.split(".")
        gateway_ip = ".".join(
                [ip_list[0], ip_list[1], ip_list[2], SUBNET_GATEWAY_TAIL_IP])
        return gateway_ip

    def _get_free_public_ip(self):
        result = self.installer.get_free_public_ip()
        self.vpn_public_ip = result["public_ip_address"]
        self.vpn_public_id = result["id"]

    def _release_public_ip(self):
        self.installer.release_public_ip()

    def cloud_preinstall(self):
        self._create_vpc()
        self._create_subnet()



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

    def install_vpc(self):
        self._install_vpc()
    def _install_vpc(self):


    def uninstall_vpc(self):
        self._uninstall_vpc()

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






