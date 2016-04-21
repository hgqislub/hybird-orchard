__author__ = 'Administrator'

from oslo.config import cfg
from hwcloud.hws_service.ecs_service import ECSService
from hwcloud.hws_service.evs_service import EVSService
from hwcloud.hws_service.ims_service import IMSService
from hwcloud.hws_service.vpc_service import VPCService
from hwcloud.hws_service.vbs_service import VBSService

hws_opts = [cfg.StrOpt('ecs_host', help='ecs_host', default='ecs.cn-north-1.myhwclouds.com.cn'),
            cfg.StrOpt('evs_host', help='evs_host', default='evs.cn-north-1.myhwclouds.com.cn'),
            cfg.StrOpt('ims_host', help='ims_host', default='ims.cn-north-1.myhwclouds.com.cn'),
            cfg.StrOpt('vpc_host', help='vpc_host', default='vpc.cn-north-1.myhwclouds.com.cn'),
            cfg.StrOpt('vbs_host', help='vbs_host', default='vbs.cn-north-1.myhwclouds.com.cn')
            ]
CONF = cfg.CONF
hws_group = 'hws'
CONF.register_opts(hws_opts, hws_group)

class HWSClient(object):
    def __init__(self, ak, sk, region, protocol, port):
        self.ak = ak
        self.sk = sk
        self.protocol = protocol
        self.port = port
        self.region = region

        self.ecs_host = CONF.hws.ecs_host
        self.evs_host = CONF.hws.evs_host
        self.ims_host = CONF.hws.ims_host
        self.vpc_host = CONF.hws.vpc_host
        self.vbs_host = CONF.hws.vbs_host

        self.ecs = ECSService(ak, sk, self.region, self.protocol, self.ecs_host, self.port)
        self.evs = EVSService(ak, sk, self.region, self.protocol, self.evs_host, self.port)
        self.ims = IMSService(ak, sk, self.region, self.protocol, self.ims_host, self.port)
        self.vpc = VPCService(ak, sk, self.region, self.protocol, self.vpc_host, self.port)
        self.vbs = VBSService(ak, sk, self.region, self.protocol, self.vbs_host, self.port)

if __name__ == '__main__':
    ak = 'DQEDQVNGMIW7KZXWO1AX'
    sk = 't4up1pD7KYs8Nj735aEcTQeYYJrnYjEQvO07L9Q0'
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