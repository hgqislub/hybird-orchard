import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))

from hwcloud.hws_service.hws_client import HWSClient
from cloudmanager.install.retry_decorator import RetryDecorator
from heat.openstack.common import log as logging
from cloud_manager_exception import *
import time
RSP_STATUS = "status"
RSP_BODY = "body"
RSP_STATUS_OK = "2"
MAX_RETRY = 10

#unit=second
SLEEP_TIME = 60
LOG = logging.getLogger(__name__)
import pdb
class HwsInstaller(object):
    def __init__(self, cloud_info):
        pdb.set_trace()
        self.hws_client = HWSClient(cloud_info)
        self.project_id = cloud_info["project_id"]

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

        return result[RSP_BODY]["server"]

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

    def block_until_success(self, job_id):
        server_id = None
        for i in range(MAX_RETRY):
            result = self.get_job_detail(job_id)
            status = result[RSP_STATUS]
            if status == "FAILED":
                break
            elif status == "SUCCESS":
                server_id = result['entities']['sub_jobs'][0]["entities"]["server_id"]
                break
            else:
                time.sleep(SLEEP_TIME * i)

        if server_id is None:
            raise InstallCascadedFailed(current_step="create vm")
        return server_id

    @RetryDecorator(max_retry_count=MAX_RETRY,
        raise_exception=InstallCascadedFailed(
        current_step="get free public ip"))
    def get_free_public_ip(self):
        result = self.hws_client.vpc.list_public_ips(self.project_id)
        status = str(result[RSP_STATUS])
        if not status.startswith(RSP_STATUS_OK):
            LOG.error(result)
            raise InstallCascadedFailed(current_step="get free public ip")
        free_ip = None
        public_ips = result[RSP_BODY]["publicips"]

        for ip in public_ips:
            if ip["port_id"] is None:
                free_ip = ip
                return free_ip

        if free_ip is None:
            publicip = dict()
            bandwidth = dict()
            publicip["type"]="5_bgp"
            bandwidth["name"]="vpn_public_ip"
            bandwidth["size"]=100
            bandwidth["share_type"]="PER"
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
            raise InstallCascadedFailed(current_step="release public ip")