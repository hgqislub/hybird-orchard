# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

import sys

sys.path.append('/usr/bin/install_tool')

import os
import json
import cps_server
import log as logger

from collections import deque

logger.init('cascaded_config')


class ExecuteStack(object):
    def __init__(self, max_retry_time):
        self.todo_list = deque([])
        self.done_list = []
        self.error_list = []
        self.zombie_list = []
        self.max_retry_time = max_retry_time

    def add_todo_command(self, fun, params=None):
        self.todo_list.append({"call": fun, "kwargs": params, "retry_time": 0})

    def start(self):
        while len(self.todo_list):
            todo = self.todo_list.popleft()

            if todo["retry_time"] >= self.max_retry_time:
                self.zombie_list.append(todo)
                continue

            try:
                if todo["kwargs"] is None:
                    execute_result = eval(todo["call"])
                else:
                    execute_result = eval(todo["call"])(**todo["kwargs"])
            except TypeError as e:
                self.error_list.append(todo)
            except Exception as e:
                execute_result = False

            if execute_result:
                self.done_list.append(todo)
            else:
                todo["retry_time"] += 1
                self.todo_list.append(todo)

    def persist_stack(self, file_name):
        todo_list = []
        for todo in self.todo_list:
            todo_list.append(todo)
        stack_info = {"todo_list": todo_list,
                      "done_list": self.done_list,
                      "error_list": self.error_list,
                      "zombie_list": self.zombie_list}
        stack_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
        with open(stack_file, 'w+') as fd:
            fd.write(json.dumps(stack_info, indent=4))


def update_ceilometer_agent_central_domain(cascading_domain, cascaded_domain):
    service = "ceilometer"
    template = "ceilometer-agent-central"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain,
        "os_region_name": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ceilometer_agent_compute_domain(cascading_domain, cascaded_domain):
    service = "ceilometer"
    template = "ceilometer-agent-compute"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain,
        "os_region_name": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ceilometer_agent_notification_domain(cascading_domain, cascaded_domain):
    service = "ceilometer"
    template = "ceilometer-agent-notification"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain,
        "os_region_name": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ceilometer_agent_hardware_domain(cascading_domain):
    service = "ceilometer"
    template = "ceilometer-agent-hardware"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ceilometer_alarm_evaluator_domain(cascading_domain, cascaded_domain):
    service = "ceilometer"
    template = "ceilometer-alarm-evaluator"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain,
        "os_region_name": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ceilometer_alarm_fault_domain(cascading_domain, cascaded_domain):
    service = "ceilometer"
    template = "ceilometer-alarm-fault"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain,
        "os_region_name": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ceilometer_alarm_notifier_domain(cascading_domain):
    service = "ceilometer"
    template = "ceilometer-alarm-notifier"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ceilometer_api_domain(cascading_domain):
    service = "ceilometer"
    template = "ceilometer-api"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ceilometer_collector_domain(cascading_domain):
    service = "ceilometer"
    template = "ceilometer-collector"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_cinder_api_domain(cascading_domain, cascaded_domain):
    service = "cinder"
    template = "cinder-api"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "glance_host": "https://image.%s" % cascading_domain,
        "storage_availability_zone": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_cinder_backup_domain(cascading_domain, cascaded_domain):
    service = "cinder"
    template = "cinder-backup"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "glance_host": "https://image.%s" % cascading_domain,
        "storage_availability_zone": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_cinder_scheduler_domain(cascading_domain, cascaded_domain):
    service = "cinder"
    template = "cinder-scheduler"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "glance_host": "https://image.%s" % cascading_domain,
        "storage_availability_zone": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_cinder_volume_domain(cascading_domain, cascaded_domain):
    service = "cinder"
    template = "cinder-volume"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "glance_host": "https://image.%s" % cascading_domain,
        "storage_availability_zone": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_info_collect_server_domain(cascading_domain):
    service = "collect"
    template = "info-collect-server"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_info_collect_client_domain(cascading_domain):
    service = "collect"
    template = "info-collect-client"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_cps_client_domain(cascading_domain):
    service = "cps"
    template = "cps-client"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_cps_server_domain(cascading_domain):
    service = "cps"
    template = "cps-server"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_network_client_domain(cascading_domain, cascaded_domain, gateway):
    service = "cps"
    template = "network-client"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain,
        "os_region_name": cascaded_region,
        "default_gateway": gateway
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_network_server_domain(cascading_domain, cascaded_domain):
    service = "cps"
    template = "network-server"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain,
        "os_region_name": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_cps_web_domain(cascading_domain, cascaded_domain):
    service = "cps"
    template = "cps-web"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "glance_domain": "https://image.%s:443" % cascading_domain,
        "keystone_domain": "https://identity.%s:443" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain,
        "os_region_name": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_gaussdb_domain(cascading_domain):
    service = "gaussdb"
    template = "gaussdb"
    updated_params = {
        "auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_glance_domain(cascading_domain):
    service = "glance"
    template = "glance"
    updated_params = {
        "api_auth_host": "identity.%s" % cascading_domain,
        "registry_auth_host": "identity.%s" % cascading_domain,
        "swift_store_auth_address": "https://identity.%s:443/identity-admin/v2.0"
                                    % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_haproxy_haproxy(cascaded_domain, cascaded_ip, gateway):
    service = "haproxy"
    template = "haproxy"

    external_api_ip = [{"backendservice": "all",
                        "frontendport": "443",
                        "systeminterface": "external_api",
                        "mask": "24",
                        "frontendip": cascaded_ip,
                        "gateway": gateway}]

    frontssl = [{"certfile": "",
                 "ssl": "true",
                 "backendservice": "all",
                 "frontendport": "443",
                 "keyfile": "",
                 "frontendip": cascaded_ip}]

    updated_params = {
        "localurl": cascaded_domain,
        "external_api_ip": json.dumps(external_api_ip),
        "frontssl": json.dumps(frontssl)
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_heat_domain(cascading_domain):
    service = "heat"
    template = "heat"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_log_server_domain(cascading_domain):
    service = "log"
    template = "log-server"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_log_agent_domain(cascading_domain):
    service = "log"
    template = "log-agent"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_mongodb_domain(cascading_domain):
    service = "mongodb"
    template = "mongodb"
    updated_params = {
        "auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_neutron_reschedule_domain(cascading_domain):
    service = "neutron"
    template = "neutron-reschedule"
    updated_params = {
        "auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_neutron_metadata_agent_domain(cascading_domain, cascaded_domain):
    service = "neutron"
    template = "neutron-metadata-agent"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain,
        "os_region_name": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_neutron_server_domain(cascading_domain, cascaded_domain):
    service = "neutron"
    template = "neutron-server"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "nova_admin_auth_url": "https://identity.%s:443/identity-admin/v2.0" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_nova_api_domain(cascading_domain, cascaded_domain):
    service = "nova"
    template = "nova-api"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "default_availability_zone": cascaded_region,
        "glance_host": "https://image.%s" % cascading_domain,
        "keystone_ec2_url": "https://identity.%s:443/identity-admin/v2.0"
                            % cascading_domain,
        "neutron_admin_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                                  % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_nova_compute_domain(cascading_domain, cascaded_domain):
    service = "nova"
    template = "nova-compute"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "default_availability_zone": cascaded_region,
        "glance_host": "https://image.%s" % cascading_domain,
        "neutron_admin_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                                  % cascading_domain,
        "novncproxy_base_url": "https://nova-novncproxy.%s:8002/vnc_auto.html"
                               % cascaded_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_nova_conductor_domain(cascading_domain, cascaded_domain):
    service = "nova"
    template = "nova-conductor"
    updated_params = {
        "glance_host": "https://image.%s" % cascading_domain,
        "neutron_admin_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                                  % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_nova_novncproxy_domain(cascading_domain, cascaded_domain):
    service = "nova"
    template = "nova-novncproxy"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "glance_host": "https://image.%s" % cascading_domain,
        "neutron_admin_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                                  % cascading_domain,
        "novncproxy_base_url": "https://nova-novncproxy.%s:8002/vnc_auto.html"
                               % cascaded_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_nova_scheduler_domain(cascading_domain, cascaded_domain):
    service = "nova"
    template = "nova-scheduler"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "default_availability_zone": cascaded_region,
        "glance_host": "https://image.%s"
                       % cascading_domain,
        "neutron_admin_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                                  % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ntp_server_domain(cascading_domain, cascading_ip, cascaded_ip):
    service = "ntp"
    template = "ntp-server"
    updated_params = {
        "active_ip": "%s/24" % cascaded_ip,
        "auth_host": "identity.%s" % cascading_domain,
        "network": "external_api",
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                       % cascading_domain,
        "server": cascading_ip
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ntp_client_domain(cascading_domain):
    service = "ntp"
    template = "ntp-client"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                       % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_swift_proxy_domain(cascading_domain):
    service = "swift"
    template = "swift-proxy"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_upg_client_domain(cascading_domain):
    service = "upg"
    template = "upg-client"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                       % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_upg_server_domain(cascading_domain):
    service = "upg"
    template = "upg-server"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                       % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_backup_server_domain(cascading_domain, cascaded_domain):
    service = "backup"
    template = "backup-server"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                       % cascading_domain,
        "os_region_name": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_backup_client_domain(cascading_domain, cascaded_domain):
    service = "backup"
    template = "backup-client"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                       % cascading_domain,
        "os_region_name": cascaded_region
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_oam_network_server_domain(cascading_domain):
    service = "fusionnetwork"
    template = "oam-network-server"
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                       % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_nova_compute_ironic_domain(cascading_domain):
    service = "nova"
    template = "nova-compute-ironic"
    updated_params = {
        "glance_host": "https://image.%s" % cascading_domain,
        "neutron_admin_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                                  % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ironic_api_domain(cascading_domain, cascaded_domain):
    service = "ironic"
    template = "ironic-api"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "glance_host": "https://image.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                       % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ironic_conductor_domain(cascading_domain, cascaded_domain):
    service = "ironic"
    template = "ironic-conductor"
    cascaded_region = _get_cascaded_region_form_cascaded_domain(cascaded_domain)
    updated_params = {
        "auth_host": "identity.%s" % cascading_domain,
        "glance_host": "https://image.%s" % cascading_domain,
        "os_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                       % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_ironicproxy_domain(cascading_domain):
    service = "ironic"
    template = "ironicproxy"
    updated_params = {
        "neutron_admin_auth_url": "https://identity.%s:443/identity-admin/v2.0"
                                  % cascading_domain
    }
    return cps_server.update_template_params(service, template, updated_params)


def update_local_domain(cascaded_domain):
    arr = cascaded_domain.split(".")
    cascaded_local_az = arr[0]
    cascaded_local_dc = arr[1]
    domain_postfix = ".".join(arr[2:])
    return cps_server.set_local_domain(cascaded_local_dc, cascaded_local_az, domain_postfix)


def update_dns_dns_server(cascading_domain, cascading_ip, cascaded_domain, cascaded_ip, gateway):
    service = "dns"
    template = "dns-server"
    address = "/%(cascading_domain)s/%(cascading_ip)s,/%(cascaded_domain)s/%(cascaded_ip)s" \
              % {"cascading_domain": cascading_domain,
                 "cascading_ip": cascading_ip,
                 "cascaded_domain": cascaded_domain,
                 "cascaded_ip": cascaded_ip}

    network = [{"ip": cascaded_ip,
                "systeminterface": "external_api",
                "mask": "24",
                "gateway": gateway}]

    updated_params = {
        "address": address,
        "network": json.dumps(network)
    }

    return cps_server.update_template_params(service, template, updated_params)


def update_apacheproxy_apacheproxy(cascaded_ip, gateway):
    service = "apacheproxy"
    template = "apacheproxy"

    external_api_ip = [{"systeminterface": "external_api",
                        "mask": "24",
                        "gateway": gateway,
                        "ip": cascaded_ip}]

    proxy_remote_match = [{"regex": ".*",
                           "ProxySourceAddress": cascaded_ip,
                           "vhost_port": 8081}]

    updated_params = {
        "external_api_ip": json.dumps(external_api_ip),
        "proxy_remote_match": json.dumps(proxy_remote_match)
    }
    return cps_server.update_template_params(service, template, updated_params)


def cps_commit():
    return cps_server.cps_commit()


def _get_cascaded_region_form_cascaded_domain(cascaded_domain):
    arr = cascaded_domain.split(".")
    cascaded_local_az = arr[0]
    cascaded_local_dc = arr[1]
    return ".".join([cascaded_local_az, cascaded_local_dc])


if __name__ == '__main__':
    cascading_domain = sys.argv[1]
    cascading_ip = sys.argv[2]
    cascaded_domain = sys.argv[3]
    cascaded_ip = sys.argv[4]
    gateway = sys.argv[5]

    stack = ExecuteStack(30)

    param_cascading = {"cascading_domain": cascading_domain}
    param_cascaded = {"cascaded_domain": cascaded_domain}
    param_cascading_and_cascaded_ip = {"cascading_domain": cascading_domain,
                                       "cascading_ip": cascading_ip,
                                       "cascaded_ip": cascaded_ip}
    param_cascading_and_cascaded = {"cascading_domain": cascading_domain,
                                    "cascaded_domain": cascaded_domain}
    param_cascading_and_cascaded_and_gateway = {"cascading_domain": cascading_domain,
                                                "cascaded_domain": cascaded_domain,
                                                "gateway": gateway}
    param_cascaded_and_ip_and_gateway = {"cascaded_domain": cascaded_domain, "cascaded_ip": cascaded_ip,
                                         "gateway": gateway}
    param_cascaded_ip_and_gateway = {"cascaded_ip": cascaded_ip, "gateway": gateway}
    param_all = {"cascading_domain": cascading_domain, "cascading_ip": cascading_ip,
                 "cascaded_domain": cascaded_domain, "cascaded_ip": cascaded_ip,
                 "gateway": gateway}

    # add stack todo_list
    stack.add_todo_command(update_local_domain.func_name, param_cascaded)
    stack.add_todo_command(update_dns_dns_server.func_name, param_all)
    stack.add_todo_command(update_ceilometer_agent_central_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_ceilometer_agent_compute_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_ceilometer_agent_notification_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_ceilometer_agent_hardware_domain.func_name, param_cascading)
    stack.add_todo_command(update_ceilometer_alarm_evaluator_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_ceilometer_alarm_fault_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_ceilometer_alarm_notifier_domain.func_name, param_cascading)
    stack.add_todo_command(update_ceilometer_api_domain.func_name, param_cascading)
    stack.add_todo_command(update_ceilometer_collector_domain.func_name, param_cascading)
    stack.add_todo_command(update_cinder_api_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_cinder_backup_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_cinder_scheduler_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_cinder_volume_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_info_collect_server_domain.func_name, param_cascading)
    stack.add_todo_command(update_info_collect_client_domain.func_name, param_cascading)
    stack.add_todo_command(update_cps_client_domain.func_name, param_cascading)
    stack.add_todo_command(update_cps_server_domain.func_name, param_cascading)
    stack.add_todo_command(update_network_client_domain.func_name, param_cascading_and_cascaded_and_gateway)
    stack.add_todo_command(update_network_server_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_cps_web_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_gaussdb_domain.func_name, param_cascading)
    stack.add_todo_command(update_glance_domain.func_name, param_cascading)
    stack.add_todo_command(update_haproxy_haproxy.func_name, param_cascaded_and_ip_and_gateway)
    stack.add_todo_command(update_heat_domain.func_name, param_cascading)
    stack.add_todo_command(update_log_server_domain.func_name, param_cascading)
    stack.add_todo_command(update_log_agent_domain.func_name, param_cascading)
    stack.add_todo_command(update_mongodb_domain.func_name, param_cascading)
    stack.add_todo_command(update_neutron_reschedule_domain.func_name, param_cascading)
    stack.add_todo_command(update_neutron_metadata_agent_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_neutron_server_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_nova_api_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_nova_compute_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_nova_conductor_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_nova_novncproxy_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_nova_scheduler_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_ntp_server_domain.func_name, param_cascading_and_cascaded_ip)
    stack.add_todo_command(update_ntp_client_domain.func_name, param_cascading)
    stack.add_todo_command(update_swift_proxy_domain.func_name, param_cascading)
    stack.add_todo_command(update_upg_client_domain.func_name, param_cascading)
    stack.add_todo_command(update_upg_server_domain.func_name, param_cascading)
    stack.add_todo_command(update_backup_server_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_backup_client_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_oam_network_server_domain.func_name, param_cascading)
    stack.add_todo_command(update_nova_compute_ironic_domain.func_name, param_cascading)
    stack.add_todo_command(update_ironic_api_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_ironic_conductor_domain.func_name, param_cascading_and_cascaded)
    stack.add_todo_command(update_ironicproxy_domain.func_name, param_cascading)
    stack.add_todo_command(update_apacheproxy_apacheproxy.func_name, param_cascaded_ip_and_gateway)

    stack.start()
    cps_server.cps_commit()

    stack.add_todo_command(cps_commit.func_name)
    stack.start()
    stack.persist_stack("stack_info.json")
