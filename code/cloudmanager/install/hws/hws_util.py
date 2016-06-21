import os

from heat.engine.resources.hwcloud.hws_service.hws_client import HWSClient
from heat.engine.resources.cloudmanager.util.retry_decorator import RetryDecorator
from heat.openstack.common import log as logging
from heat.engine.resources.cloudmanager.util.cloud_manager_exception import *
from heat.engine.resources.cloudmanager.exception import * 
import time
import heat.engine.resources.cloudmanager.constant as constant
from heat.engine.resources.cloudmanager.commonutils import *

RSP_STATUS = "status"
RSP_BODY = "body"
RSP_STATUS_OK = "2"
MAX_RETRY = 50

#unit=second
SLEEP_TIME = 3
MAX_CHECK_TIMES = 2000

LOG = logging.getLogger(__name__)


def start_hws_gateway(host_ip, user, passwd):
    execute_cmd_without_stdout(
                host=host_ip, user=user, password=passwd,
                cmd='cd %(dis)s; sh %(script)s start'
                % {"dis": constant.PatchesConstant.REMOTE_HWS_SCRIPTS_DIR,
                    "script":
                    constant.PatchesConstant.START_HWS_GATEWAY_SCRIPT}
    )

def stop_hws_gateway(host_ip, user, password):
        LOG.info("start hws java gateway ...")
        execute_cmd_without_stdout(
                    host=host_ip, user=user, password=password,
                    cmd='cd %(dis)s; sh %(script)s stop'
                    % {"dis": constant.PatchesConstant.REMOTE_HWS_SCRIPTS_DIR,
                        "script":
                        constant.PatchesConstant.START_HWS_GATEWAY_SCRIPT}
                    )

class HwsInstaller(object):
    def __init__(self, ak, sk, region, protocol, host, port, project_id):
        self.hws_client = HWSClient(ak, sk, region, protocol, host, port)
        self.project_id = project_id

    @RetryDecorator(max_retry_count=MAX_RETRY,
                raise_exception=InstallCascadedFailed(
                    current_step="create vm"))
    def create_vm(self, image_ref, flavor_ref, name, vpcid, nics_subnet_list, root_volume_type,availability_zone,
                      personality_path=None, personality_contents=None, adminPass=None, public_ip_id=None, count=None,
                      data_volumes=None, security_groups=None, key_name=None):
        result = self.hws_client.ecs.create_server(self.project_id, image_ref, flavor_ref, name, vpcid, nics_subnet_list, root_volume_type,
                      availability_zone, personality_path, personality_contents, adminPass, public_ip_id, count,
                      data_volumes, security_groups, key_name)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="create cascaded vm")

        return result[RSP_BODY]["job_id"]

    @RetryDecorator(max_retry_count=MAX_RETRY,
                raise_exception=UninstallCascadedFailed(
                    current_step="delete vm"))
    def delete_vm(self, server_id_list, delete_public_ip, delete_volume):
        result = self.hws_client.ecs.delete_server\
            (self.project_id, server_id_list, delete_public_ip, delete_volume)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise UninstallCascadedFailed(current_step="delete cascaded vm")

        return result[RSP_BODY]["job_id"]

    @RetryDecorator(max_retry_count=MAX_RETRY,
                raise_exception=InstallCascadedFailed(
                    current_step="create vm"))
    def create_vpc(self, name, cidr):
        result = self.hws_client.vpc.create_vpc(self.project_id, name, cidr)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="create vpc")

        return result[RSP_BODY]["vpc"]["id"]

    @RetryDecorator(max_retry_count=MAX_RETRY,
                raise_exception=UninstallCascadedFailed(
                    current_step="delete vpc"))
    def delete_vpc(self, vpc_id):
        result = self.hws_client.vpc.delete_vpc(self.project_id, vpc_id)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise UninstallCascadedFailed(current_step="delete vpc")

    @RetryDecorator(max_retry_count=MAX_RETRY,
                raise_exception=InstallCascadedFailed(
                    current_step="create subnet"))
    def create_subnet(self, name, cidr, availability_zone, gateway_ip, vpc_id,
                       dhcp_enable=None, primary_dns=None, secondary_dns=None):
        result = self.hws_client.vpc.create_subnet(self.project_id, name, cidr,
                      availability_zone, gateway_ip, vpc_id,
                      dhcp_enable, primary_dns, secondary_dns)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="create subnet")
        return result[RSP_BODY]["subnet"]["id"]

    @RetryDecorator(max_retry_count=MAX_RETRY,
                raise_exception=UninstallCascadedFailed(
                    current_step="delete subnet"))
    def delete_subnet(self, vpc_id, subnet_id):
        result = self.hws_client.vpc.delete_subnet(self.project_id, vpc_id, subnet_id)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise UninstallCascadedFailed(current_step="delete subnet")
        return result[RSP_BODY]

    @RetryDecorator(max_retry_count=MAX_RETRY,
            raise_exception=InstallCascadedFailed(
                current_step="get job detail"))
    def get_job_detail(self, job_id):
        result = self.hws_client.vpc.get_job_detail(self.project_id, job_id)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="get job detail")
        return result[RSP_BODY]

    def block_until_delete_resource_success(self, job_id):
        for i in range(MAX_CHECK_TIMES):
            result = self.get_job_detail(job_id)
            status = result[RSP_STATUS]
            if status == "FAILED":
                raise InstallCascadedFailed(current_step="delete resource")
            elif status == "SUCCESS":
                return
            else:
                time.sleep(3)
        pass

    def block_until_create_vm_success(self, job_id):
        server_id = None
        for i in range(MAX_CHECK_TIMES):
            result = self.get_job_detail(job_id)
            status = result[RSP_STATUS]
            if status == "FAILED":
                break
            elif status == "SUCCESS":
                server_id = result['entities']['sub_jobs'][0]["entities"]["server_id"]
                break
            else:
                time.sleep(SLEEP_TIME)

        if server_id is None:
            raise InstallCascadedFailed(current_step="create vm")
        return server_id

    def block_until_create_nic_success(self, job_id):
        nic_id = None
        for i in range(MAX_CHECK_TIMES):
            result = self.get_job_detail(job_id)
            status = result[RSP_STATUS]
            if status == "FAILED":
                break
            elif status == "SUCCESS":
                nic_id = result['entities']['sub_jobs'][0]["entities"]["nic_id"]
                break
            else:
                time.sleep(3)

        if nic_id is None:
            raise InstallCascadedFailed(current_step="create nic")
        return nic_id

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=InstallCascadedFailed(
        current_step="get server nics info"))
    def get_all_nics(self, server_id):
        result = self.hws_client.ecs.get_all_nics(self.project_id, server_id)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise UninstallCascadedFailed(current_step="get server incs info")
        return result[RSP_BODY]["interfaceAttachments"]

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=InstallCascadedFailed(
        current_step="get server ips"))
    def get_server_ips(self, server_id):
        result = self.hws_client.ecs.get_server_ips(self.project_id, server_id)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise UninstallCascadedFailed(current_step="get server ips")
        return result[RSP_BODY]["interfaceAttachments"]["fixed_ips"]

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=InstallCascadedFailed(
        current_step="get free public ip"))
    def alloc_public_ip(self, name):
        result = self.hws_client.vpc.list_public_ips(self.project_id)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="get free public ip")
        free_ip = None
        public_ips = result[RSP_BODY]["publicips"]

        for ip in public_ips:
            if ip["status"] == "DOWN":
                free_ip = ip
                return free_ip

        if free_ip is None:
            publicip = dict()
            bandwidth = dict()
            publicip["type"]="5_bgp"
            bandwidth["name"]=name
            bandwidth["size"]=100
            bandwidth["share_type"]="PER"
            bandwidth["charge_mode"]= "traffic"
            result = self.hws_client.vpc.create_public_ip(self.project_id, publicip, bandwidth)
            status = str(result[RSP_STATUS])
            if not status.startswith(RSP_STATUS_OK):
                LOG.error(result)
                raise InstallCascadedFailed(current_step="create public ip")
            free_ip = result[RSP_BODY]["publicip"]
            return free_ip

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=UninstallCascadedFailed(
        current_step="release public ip"))
    def release_public_ip(self, public_ip_id):
        result = self.hws_client.vpc.delete_public_ip(self.project_id, public_ip_id)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise UninstallCascadedFailed(current_step="release public ip")

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=InstallCascadedFailed(
        current_step="get security group"))
    def get_security_group(self, vpc_id):
        opts = dict()
        opts["vpc_id"] = vpc_id
        result = self.hws_client.vpc.list_security_groups(self.project_id,opts = opts)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="get security group")
        security_groups = result[RSP_BODY]["security_groups"]

        for security_group in security_groups:
            if security_group["name"] == "default":
                return security_group["id"]

        return security_groups[0]["id"]

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=InstallCascadedFailed(
        current_step="create security group rule"))
    def create_security_group_rule(self, security_group_id, direction, ethertype):
        result = self.hws_client.vpc.create_security_group_rule(
                self.project_id, security_group_id, direction, ethertype)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="create security group rule")

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=InstallCascadedFailed(
        current_step="get_external_api_port_id"))
    def get_external_api_port_id(self, server_id, external_api_nic_id):
        result = self.hws_client.ecs.get_nic_info(self.project_id, server_id, external_api_nic_id)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="get_external_api_port_id")
        interfaceAttachment = result[RSP_BODY]["interfaceAttachment"]
        return interfaceAttachment["port_id"]

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=InstallCascadedFailed(
        current_step="bind public ip to cascaded"))
    def bind_public_ip(self, public_ip_id, port_id):
        result = self.hws_client.vpc.bind_public_ip(
                self.project_id, public_ip_id, port_id)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="bind public ip to cascaded")

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=InstallCascadedFailed(
        current_step="add nics to vm"))
    def add_nics(self, server_id, subnet_id, security_groups, ip_address = None):
        nic = dict()
        nic["subnet_id"] = subnet_id
        nic["security_groups"] = security_groups
        if ip_address:
            nic["ip_address"] = ip_address
        nics = [nic]
        result = self.hws_client.ecs.add_nics(
                self.project_id, server_id, nics)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="add nics to cascaded")

        return result[RSP_BODY]["job_id"]

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=InstallCascadedFailed(
        current_step="reboot cascaded"))
    def reboot(self, server_id, type):
        result = self.hws_client.ecs.reboot(self.project_id, server_id, type)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="reboot cascaded")

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=InstallCascadedFailed(
        current_step="unbound vpn ip-mac"))
    def unbound_ip_mac(self, port_id, mac_address):
        allowed_address_pairs = []
        #allow all ip_addresses to access
        pair1={"ip_address":"0.0.0.1/1",
                "mac_address":mac_address}
        pair2={"ip_address":"128.0.0.0/1",
                "mac_address":mac_address}
        allowed_address_pairs.append(pair1)
        allowed_address_pairs.append(pair2)

        result = self.hws_client.vpc.update_port(port_id, allowed_address_pairs=allowed_address_pairs)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="unbound vpn ip-mac")