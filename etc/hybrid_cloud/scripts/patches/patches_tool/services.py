__author__ = 'nash.xiejun'
import json
import os
import sys
import traceback

from keystoneclient.v2_0.endpoints import Endpoint
from nova.proxy import clients
from nova.proxy import compute_context

# from install_tool import cps_server, fsutils, fs_system_util
# TODO:
sys.path.append('/usr/bin/install_tool')
import cps_server
import fsutils
import fs_system_util
import utils
import time

import log

from constants import ScriptFilePath

class RefServices(object):

    def __init__(self, region_name=None, bypass_url=None):
        """

        :param region_name: use to specify service in which region want to reference
        :param bypass_url: use to specify url of service
        :return:
        """
        self.tenant = os.environ['OS_TENANT_NAME']
        self.user = os.environ['OS_USERNAME']
        self.pwd = os.environ['OS_PASSWORD']
        self.auth_url = os.environ['OS_AUTH_URL']
        self.bypass_url = bypass_url
        self.region_name = os.environ['OS_REGION_NAME']
        keystone_credentials = self.get_keystone_credentials()
        self.keystone = self.get_keystone_client(keystone_credentials)
        nova_credentials = self.get_nova_credentials_v2()
        self.nova = self.get_nova_sync_client(nova_credentials)
        self.neutron = self.get_neutron_client(nova_credentials)

    def get_keystone_credentials(self):
        d = {}
        d['version'] = '2'
        d['username'] = self.user
        d['password'] = self.pwd
        d['auth_url'] = self.auth_url
        d['tenant'] = self.tenant
        if self.region_name is not None:
            d['region_name'] = self.region_name

        d['bypass_url'] = self.bypass_url

        log.info('keystone credentials: %s' % d)

        return d

    def get_nova_credentials_v2(self):
        """
        d = {'version': '2', 'username' : os.environ['OS_USERNAME'], 'api_key' : os.environ['OS_PASSWORD'], 'auth_url' : os.environ['OS_AUTH_URL'], 'project_id' : os.environ['OS_TENANT_NAME']}
        :return:
        """
        d = {}
        d['version'] = '2'
        d['username'] = self.user
        d['password'] = self.pwd
        d['auth_url'] = self.auth_url
        d['tenant'] = self.tenant
        if self.region_name is not None:
            d['region_name'] = self.region_name

        if self.bypass_url is not None:
            d['bypass_url'] = self.bypass_url

        return d

    def get_neutron_client(self, kwargs):
        req_context = compute_context.RequestContext(**kwargs)
        openstack_clients = clients.OpenStackClients(req_context)
        return openstack_clients.neutron()

    def get_nova_sync_client(self, kwargs):
        """
        kwargs = {
            'username': CONF.nova_admin_username,
            'password': CONF.nova_admin_password,
            'tenant': CONF.nova_admin_tenant_name,
            'auth_url': CONF.keystone_auth_url,
            'region_name': CONF.proxy_region_name
        }

        :param args:
        :return:
        """
        req_context = compute_context.RequestContext(**kwargs)
        openstack_clients = clients.OpenStackClients(req_context)
        return openstack_clients.nova()

    def get_keystone_client(self, kwargs):
        """
        kwargs = {
            'username': CONF.nova_admin_username,
            'password': CONF.nova_admin_password,
            'tenant': CONF.nova_admin_tenant_name,
            'auth_url': CONF.keystone_auth_url,
            'region_name': CONF.proxy_region_name
        }

        :param args:
        :return:
        """
        req_context = compute_context.RequestContext(**kwargs)
        openstack_clients = clients.OpenStackClients(req_context)

        return openstack_clients.keystone().client_v2

    def nova_list(self):
        return self.nova.servers.list(detailed=True)

    def nova_aggregate_create(self, name, availability_zone):
        result = None
        log.info("create ag, name: %s, availability_zone: %s" % (name, availability_zone))
        for i in range(100):
            try:
                aggregate_result = self.nova.aggregates.create(name, availability_zone)

                log.info('created Aggregate result is : %s ' % aggregate_result)

                if aggregate_result.name == name:
                    result = aggregate_result
                    log.info("created Aggregate success")
                    return result
            except Exception as e:
                log.error('Exception when create AG for %s, error: %s'
                          % (name, traceback.format_exc()))
                time.sleep(6)
                continue
        return result

    def nova_host_list(self):
        result = False

        return result

    def nova_aggregate_add_host(self, aggregate, host):
        result = False

        try:
            add_result = self.nova.aggregates.add_host(aggregate, host)
            log.info('Add host<%s> to aggregate<%s>, result : %s '
                     % (host, aggregate, add_result))
            result = True
        except Exception as e:
            log.error('Exception when add host<%s> to aggregate<%s>, Exception : %s '
                      % (host, aggregate, e.message))

        return result

    def nova_aggregate_exist(self, name, availability_zone):
        aggregates = None
        for i in range(50):
            try:
                aggregates = self.nova.aggregates.list()
                break
            except Exception as e:
                log.error("get nova aggregate list error, try again")
                time.sleep(6)

        if aggregates is None:
            log.error("get nova aggregate list failed.")
            return False

        for aggregate in aggregates:
            if aggregate.availability_zone == availability_zone:
                return True

        return False

    def get_tenant_id_for_service(self):
        """
        To get tenant id by tenant name 'service'.

        step1: use list() to get all tenants:
            [<Tenant {u'enabled': True, u'description': None, u'name': u'admin', u'id': u'f7851684a9894e5a9590a97789552879'}>,
            <Tenant {u'enabled': True, u'description': None, u'name': u'service', u'id': u'04720946e4f34cf4afed11752b1f5136'}>]
        step2: then filter the one which name is 'service'

        :return: string, tenant id of tenant named 'service'
        """
        tenant_name = 'service'
        return self.get_tenant_id_by_tenant_name(tenant_name)

    def get_tenant_id_for_admin(self):
        return self.get_tenant_id_by_tenant_name('admin')

    def get_tenant_id_by_tenant_name(self, tenant_name):
        tenant_id = None
        tenants = self.keystone.tenants.list()

        if tenants is None:
            log.info('No any tenant in keystone.')
        else:
            for tenant in tenants:
                if tenant.name == tenant_name:
                    tenant_id = tenant.id
                    break
                else:
                    continue

        return tenant_id

    def get_service_id(self, service_type):
        service_id = None
        services = self.keystone.services.list()
        for service in services:
            if service.type == service_type:
                service_id = service.id
                break
            else:
                continue

        return service_id

    def create_endpoint(self, region, service_id, publicurl, adminurl=None,
                        internalurl=None):
        result = False
        create_result = self.keystone.endpoints.create(region, service_id, publicurl, adminurl, internalurl)
        if isinstance(create_result, Endpoint):
            result = True

        return result

    def create_endpoint_for_service(self, service_type, region, url):
        public_url = url
        admin_url = url
        internal_url = url
        try:
            service_id = self.get_service_id(service_type)

            if self.endpoint_exist(service_id, region):
                log.info('Endpoint for service<%s> region <%s> is exist, no need to create again.' %
                            (service_type, region))
                return

            if service_id is None:
                raise ValueError('Service id of type <%s> is None.' % service_type)

            create_result = self.create_endpoint(region, service_id, public_url, admin_url, internal_url)
            if create_result is True:
                log.info('SUCCESS to create endpoint for type <%s> region: <%s>' % (service_type, region))
            else:
                log.info('FAILED to create endpoint for type <%s> region: <%s>' % (service_type, region))
        except:
            err_info = 'Exception occur when create endpoint for type<%s> region <%s>, EXCEPTION %s' % \
                       (service_type, region, traceback.format_exc())
            log.info(err_info)

    def endpoint_exist(self, service_id, region):
        result = False
        endpoints = self.keystone.endpoints.list()
        for endpoint in endpoints:
            if endpoint.service_id == service_id and endpoint.region == region:
                result = True
                break
            else:
                continue
        return result

    def del_endpoint(self, regions):
        """

        :param regions: [], list of regions
        :return:
        """
        result = False
        endpoints = self.keystone.endpoints.list()
        for endpoint in endpoints:
            if endpoint.region in regions:
                self.keystone.endpoints.delete(endpoint.id)
            else:
                continue
        return result


class RefCPSService(object):

    @staticmethod
    def update_template_params(service_name, template_name, params):
        cps_server.update_template_params(service_name, template_name, params)

    @staticmethod
    def get_template_params(server, template):
        return cps_server.get_template_params(server, template)

    @staticmethod
    def cps_commit():
        return cps_server.cps_commit()

    @staticmethod
    def get_cps_http(url):
        return cps_server.get_cps_http(url)

    @staticmethod
    def post_cps_http(url, body):
        return cps_server.post_cps_http(url, body)

    @staticmethod
    def get_local_domain():
        return cps_server.get_local_domain()

    @staticmethod
    def host_list():
        return cps_server.cps_host_list()

    @staticmethod
    def role_host_add(role_name, hosts):
        """
        :param role_name: string of role name, e.g. nova-proxy001
        :param hosts: list of hosts, e.g. ['9A5A2614-D21D-B211-83F3-000000821800', EF1503DA-AEC8-119F-8567-000000821800]
        :return:
        """
        cps_server.role_host_add(role_name, hosts)
        cps_server.cps_commit

    @staticmethod
    def role_host_list(role):
        """

        :param role: string of role name, e.g. nova-proxy001
        :return:
        """
        return cps_server.get_role_host_list(role)


class RefCPSServiceExtent(object):
    @staticmethod
    def list_template_instance(service, template):
        url = '/cps/v1/instances?service=%s&template=%s' % (service, template)
        res_text = RefCPSService.get_cps_http(url)
        if res_text is not None:
            return json.loads(res_text)
        return None

    @staticmethod
    def host_template_instance_operate(service, template, action):
        url = '/cps/v1/instances?service=%s&template=%s' % (service, template)
        body = {'action': action}
        return RefCPSService.post_cps_http(url, body)


class CPSServiceBusiness(object):
    def __init__(self):
        self.NOVA = 'nova'
        self.NOVA_API = 'nova-api'
        self.NEUTRON = 'neutron'
        self.NEUTRON_l2 = 'neutron-l2'
        self.NEUTRON_l3 = 'neutron-l3'
        self.CINDER = 'cinder'
        self.OPT_STOP = 'STOP'
        self.OPT_START = 'START'
        self.STATUS_ACTIVE = 'active'
        self.DNS = 'dns'
        self.DNS_SERVER_TEMPLATE = 'dns-server'
        self.region_match_ip = {}

    def get_nova_proxy_template(self, proxy_number):
        return '-'.join([self.NOVA, proxy_number])

    def get_neutron_l2_proxy_template(self, proxy_number):
        return '-'.join([self.NEUTRON_l2, proxy_number])

    def get_neutron_l3_proxy_template(self, proxy_number):
        return '-'.join([self.NEUTRON_l3, proxy_number])

    def get_cinder_template(self, proxy_number):
        return '-'.join([self.CINDER, proxy_number])

    def stop_nova_proxy(self, proxy_number):
        nova_proxy_template = self.get_nova_proxy_template(proxy_number)
        RefCPSServiceExtent.host_template_instance_operate(self.NOVA, nova_proxy_template, self.OPT_STOP)

    def start_nova_proxy(self, proxy_number):
        nova_proxy_template = self.get_nova_proxy_template(proxy_number)
        RefCPSServiceExtent.host_template_instance_operate(self.NOVA, nova_proxy_template, self.OPT_START)

    def stop_cinder_proxy(self, proxy_number):
        cinder_proxy_template = self.get_cinder_template(proxy_number)
        RefCPSServiceExtent.host_template_instance_operate(self.CINDER, cinder_proxy_template, self.OPT_STOP)

    def start_cinder_proxy(self, proxy_number):
        cinder_proxy_template = self.get_cinder_template(proxy_number)
        RefCPSServiceExtent.host_template_instance_operate(self.CINDER, cinder_proxy_template, self.OPT_START)

    def stop_neutron_l2_proxy(self, proxy_number):
        neutron_proxy_template = self.get_neutron_l2_proxy_template(proxy_number)
        RefCPSServiceExtent.host_template_instance_operate(self.NEUTRON, neutron_proxy_template, self.OPT_STOP)

    def start_neutron_l2_proxy(self, proxy_number):
        neutron_proxy_template = self.get_neutron_l2_proxy_template(proxy_number)
        RefCPSServiceExtent.host_template_instance_operate(self.NEUTRON, neutron_proxy_template, self.OPT_START)

    def stop_neutron_l3_proxy(self, proxy_number):
        neutron_proxy_template = self.get_neutron_l3_proxy_template(proxy_number)
        RefCPSServiceExtent.host_template_instance_operate(self.NEUTRON, neutron_proxy_template, self.OPT_STOP)

    def start_neutron_l3_proxy(self, proxy_number):
        neutron_proxy_template = self.get_neutron_l3_proxy_template(proxy_number)
        RefCPSServiceExtent.host_template_instance_operate(self.NEUTRON, neutron_proxy_template, self.OPT_START)

    def stop_nova_api(self):
        RefCPSServiceExtent.host_template_instance_operate(self.NOVA, self.NOVA_API, self.OPT_STOP)

    def start_nova_api(self):
        RefCPSServiceExtent.host_template_instance_operate(self.NOVA, self.NOVA_API, self.OPT_START)

    def stop_all(self, proxy_number):
        self.stop_cinder_proxy(proxy_number)
        self.stop_neutron_l2_proxy(proxy_number)
        self.stop_neutron_l3_proxy(proxy_number)
        self.stop_nova_proxy(proxy_number)
        self.stop_nova_api()

    def start_all(self, proxy_number):
        self.start_cinder_proxy(proxy_number)
        self.start_neutron_l2_proxy(proxy_number)
        self.start_neutron_l3_proxy(proxy_number)
        self.start_nova_proxy(proxy_number)
        self.start_nova_api()

    def check_status_for_template(self, service, template, aim_status):
        template_instance_info = RefCPSServiceExtent.list_template_instance(service, template)
        if template_instance_info is None or len(template_instance_info.get('instances')) < 1:
            print('Template instance info of Service<%s> Template<%s> is None.' % (service, template))
            log.error('Template instance info of Service<%s> Template<%s> is None.' % (service, template))
            log.error('template_instance_info: %s' % template_instance_info)
            return None
        status = template_instance_info.get('instances')[0].get('hastatus')
        if status == aim_status:
            log.info('Status of service<%s>, template<%s> is: %s' % (service, template, status))
            print('Status of service<%s>, template<%s> is: %s' % (service, template, status))
            return True
        else:
            log.error('Status of service<%s>, template<%s> is: %s' % (service, template, status))
            print('Status of service<%s>, template<%s> is: %s' % (service, template, status))
            return False

    def check_nova_template(self, proxy_number):
        nova_template = self.get_nova_proxy_template(proxy_number)
        self.check_status_for_template(self.NOVA, nova_template, self.STATUS_ACTIVE)

    def check_neutron_l2_template(self, proxy_number):
        neutron_l2_template = self.get_neutron_l2_proxy_template(proxy_number)

        self.check_status_for_template(self.NEUTRON, neutron_l2_template, self.STATUS_ACTIVE)

    def check_neutron_l3_template(self, proxy_number):
        neutron_l3_template = self.get_neutron_l3_proxy_template(proxy_number)
        self.check_status_for_template(self.NEUTRON, neutron_l3_template, self.STATUS_ACTIVE)

    def check_cinder_template(self, proxy_number):
        cinder_template = self.get_cinder_template(proxy_number)
        check_result = self.check_status_for_template(self.CINDER, cinder_template, self.STATUS_ACTIVE)

        return check_result

    def check_all_service_template_status(self, proxy_number):
        log.info('check cinder proxy status, cinder proxy : <%s>' % proxy_number)
        check_cinder_result = self.check_cinder_template(proxy_number)
        log.info('check cinder proxy status, cinder proxy : <%s>, status : <%s>' % (proxy_number, check_cinder_result))

        if check_cinder_result is not None and not check_cinder_result:
            proxy_match_host = self.get_proxy_match_host()
            proxy_host = proxy_match_host[proxy_number]
            command =\
                'echo \'/usr/bin/python /usr/bin/cinder-%s --config-file /etc/cinder/cinder-%s.conf  > /dev/null 2>&1 &\' > %s' \
                % (proxy_number, proxy_number, ScriptFilePath.PATH_RESTART_CINDER_PROXY_SH)


            log.info('cinder proxy=%s, host=%s, cmd=%s' % (proxy_number, proxy_host, command))

            utils.remote_execute_cmd(proxy_host, user="root", passwd="Huawei@CLOUD8!", cmd=command)

            run_restart_cinder_proxy_cmd = '/usr/bin/sh %s' % ScriptFilePath.PATH_RESTART_CINDER_PROXY_SH

            log.info('run_restart_cinder_proxy_cmd=%s' % run_restart_cinder_proxy_cmd)

            utils.remote_execute_cmd_by_root(proxy_host, user="root", passwd="Huawei@CLOUD8!", cmd=run_restart_cinder_proxy_cmd)

        self.check_neutron_l2_template(proxy_number)
        self.check_neutron_l3_template(proxy_number)
        self.check_nova_template(proxy_number)

    @staticmethod
    def get_dns_info():
        """
        by "cps template-params-show --service dns dns-server", it will get following result:
        {u'cfg':
            {
            u'address': u'/cascading.hybrid.huawei.com/162.3.120.50,
                        /identity.cascading.hybrid.huawei.com/162.3.120.50,
                        /image.cascading.hybrid.huawei.com/162.3.120.50,
                        /az01.shenzhen--fusionsphere.huawei.com/162.3.120.52,
                        /az11.shenzhen--vcloud.huawei.com/162.3.120.58,
                        /az31.singapore--aws.vodafone.com/162.3.120.64',
            u'network': u'[]',
            u'server': u''
            }
        }
        :return:
        """
        server = "dns"
        template = "dns-server"
        dns_info = RefCPSService.get_template_params(server, template)
        return dns_info

    @staticmethod
    def get_region_match_ip():
        server = "dns"
        template = "dns-server"
        dns_info = RefCPSService.get_template_params(server, template)
        addresses = dns_info['cfg']['address']
        if not addresses:
            log.error("address is none in dns info")
            return {}
        region_match_ip = {}
        address_list = addresses.split(',')
        for address in address_list:
            if address is not None:
                tmp_address_content = address.split('/')[1:]
                if len(tmp_address_content) == 2:
                    region_match_ip[tmp_address_content[0]] = tmp_address_content[1]

        return region_match_ip

    def get_az_ip(self, az_tag, proxy_match_region):
        """
        if the region is "az01.shenzhen--fusionsphere.huawei.com", the az is "az01"
        :param az_tag: string, the full name of az, e.g. az01, az11 and so on.
        :return: array list, array list of ip address, e.g. ['162.3.120.52', '162.3.120.53', ...]
        """
        if not self.region_match_ip:
            self.region_match_ip = self.get_region_match_ip()
        ip_list = []
        if proxy_match_region is None:
            for region, ip in self.region_match_ip.items():
                if az_tag in region:
                    ip_list.append(ip)
        else:
            for region, ip in self.region_match_ip.items():
                if az_tag in region and region in proxy_match_region.values():
                    ip_list.append(ip)
        return ip_list

    def get_cascading_ip(self, proxy_match_region=None):
        """

        :return: array list, array list of ip address, e.g. ['162.3.120.52', '162.3.120.53', ...]
        """
        return self.get_az_ip('cascading', proxy_match_region)

    def get_openstack_hosts(self, proxy_match_region=None):
        """

        :return: array list, array list of ip address, e.g. ['162.3.120.52', '162.3.120.53', ...]
        """
        return self.get_az_ip('--fusionsphere', proxy_match_region)

    def get_vcloud_node_hosts(self, proxy_match_region=None):
        """

        :return: array list, array list of ip address, e.g. ['162.3.120.52', '162.3.120.53', ...]
        """
        return self.get_az_ip('--vcloud', proxy_match_region)

    def get_aws_node_hosts(self, proxy_match_region=None):
        """

        :return: array list, array list of ip address, e.g. ['162.3.120.52', '162.3.120.53', ...]
        """
        return self.get_az_ip('--aws', proxy_match_region)

    def get_os_region_name(self):
        region = RefCPSService.get_local_domain()
        os_region_name = '.'.join([RefFsSystemUtils.get_az_by_domain(region),
                                   RefFsSystemUtils.get_dc_by_domain(region)])

        return os_region_name

    def get_all_proxy_nodes(self, proxy_match_region):
        proxy_node_hosts = []
        host_list = RefCPSService.host_list()
        for host in host_list['hosts']:
            roles_list = host['roles']
            proxy_host_ip = host['manageip']
            region = self._get_region_by_roles_list(roles_list, proxy_match_region)
            if region is not None:
                proxy_node_hosts.append(proxy_host_ip)
            else:
                log.info('Region of ip <%s> is None, this host of ip address is not a proxy' % proxy_host_ip)

        return proxy_node_hosts

    def get_proxy_match_host(self):
        proxy_match_host = {}
        host_list = RefCPSService.host_list()
        for host in host_list['hosts']:
            roles_list = host['roles']
            proxy_host_ip = host['manageip']
            proxy_number = self._get_proxy_number_from_roles(roles_list)
            if proxy_number is not None:
                proxy_match_host[proxy_number] = proxy_host_ip
            else:
                log.info('Proxy number is none for host: %s' % proxy_host_ip)

        return proxy_match_host

    def _get_proxy_number_from_roles(self, roles_list):
        for role in roles_list:
            if 'proxy' in role:
                return role.split('-')[1]
            else:
                continue

        return None

    def _get_region_by_roles_list(self, roles_list, proxy_match_region):
        for role in roles_list:
            if 'compute-proxy' in role:
                proxy_number = role.split('-')[1]
                if proxy_match_region.get(proxy_number):
                    return proxy_match_region[proxy_number]
        return

class RefFsUtils(object):

    @staticmethod
    def get_local_dc_az():
        return fsutils.get_local_dc_az()

class RefFsSystemUtils(object):

    @staticmethod
    def get_az_by_domain(proxy_matched_region):
        domain_url = "".join(['https://service.', proxy_matched_region, ':443'])
        return fs_system_util.get_az_by_domain(domain_url)

    @staticmethod
    def get_dc_by_domain(proxy_matched_region):
        domain_url = "".join(['https://service.', proxy_matched_region, ':443'])
        return fs_system_util.get_dc_by_domain(domain_url)

if __name__ == '__main__':
    cps = CPSServiceBusiness()
    print(cps.get_dns_info())
