__author__ = 'hgq'

from heat.engine.resources.hwcloud.hws_service.ecs_service import ECSService
from heat.engine.resources.hwcloud.hws_service.evs_service import EVSService
from heat.engine.resources.hwcloud.hws_service.ims_service import IMSService
from heat.engine.resources.hwcloud.hws_service.vpc_service import VPCService
from heat.engine.resources.hwcloud.hws_service.vbs_service import VBSService
import pdb

class HWSClient(object):
    def __init__(self, ak, sk, region, protocol, host, port):

        host_endpoint = ".".join([region, host, 'com.cn' ])
        ecs_host = 'ecs.' + host_endpoint
        evs_host = 'evs.' + host_endpoint
        ims_host = 'ims.' + host_endpoint
        vpc_host = 'vpc.' + host_endpoint
        vbs_host = 'vbs.' + host_endpoint

        self.ecs = ECSService(ak, sk, region, protocol, ecs_host, port)
        self.evs = EVSService(ak, sk, region, protocol, evs_host, port)
        self.ims = IMSService(ak, sk, region, protocol, ims_host, port)
        self.vpc = VPCService(ak, sk, region, protocol, vpc_host, port)
        self.vbs = VBSService(ak, sk, region, protocol, vbs_host, port)

if __name__ == '__main__':
    ak = '5DTFPKOQFEIN4T7EC2BM'
    sk = '00JI0Zeoezqafr03bbWZ7pFc1b4Tw0R7A9oZlFsw'
    region = 'cn-north-1'
    protocol = 'https'
    port = '443'
    hws_client = HWSClient(ak, sk, region, protocol, port)
    project_id = '91d957f0b92d48f0b184c26975d2346e'
    server_id = '72194025-ce73-41a4-a6a4-9637cdf6a0b1'

    image_id = '37ca2b35-6fc7-47ab-93c7-900324809c5c'
    flavor_id = 'c1.medium'
    vpc_id = '742cef84-512c-43fb-a469-8e9e87e35459'
    subnet_id = '7bd9410f-38bb-4fbb-aa7a-cf4a22cb20f3'
    subnet_id_list = [subnet_id]
    root_volume_type = 'SATA'
    availability_zone="cn-north-1a"
    size = 120
    # job_info = hws_client.evs.create_volume(project_id, availability_zone, size, root_volume_type, name='v_1')
    # print job_info

    # job_detail = hws_client.evs.get_job_detail(project_id, '8aace0c8523c082201523f215b0903b3')
    # print job_detail
    volume_id = '9dfd0600-f822-48fa-b831-f43d97135ee5'
    backup_name = 'bk_1'
    server_list = hws_client.ecs.list(project_id)
    print server_list
    # job_info = hws_client.vbs.create_backup(project_id, volume_id, backup_name)
    # print(job_info)
    # job_id = job_info['body']['job_id']
    # job_detail = hws_client.vbs.get_job_detail(project_id, job_id)