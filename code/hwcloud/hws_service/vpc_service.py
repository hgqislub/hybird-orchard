__author__ = 'Administrator'

import json

from hwcloud.hws_service import HWSService


class VPCService(HWSService):
    def __init__(self, ak, sk, region, protocol, host, port):
        super(VPCService, self).__init__(ak, sk, 'VPC', region, protocol, host, port)

    def list_vpc(self, project_id, opts=None):
        """

        :param project_id: string
        :param opts: dict
        :return: dict
        {
            u'body': {
                u'vpcs': [{
                    u'status': u'OK',
                    u'cidr': u'172.21.0.0/16',
                    u'id': u'742cef84-512c-43fb-a469-8e9e87e35459',
                    u'name': u'VPC_2015-10-21-11-30-28'
                }]
            },
            u'status': 200
        }
        """
        uri = "/v1/%s/vpcs" % project_id
        if opts:
            str_opts = self.convertDictOptsToString(opts)
            uri = '?'.join([uri, str_opts])
        return self.get(uri)

    def list_vpc_detail(self, project_id, vpc_id):
        """

        :param project_id: string
        :param vpc_id: string
        :return: dict
        {
            u'body': {
                u'vpc': {
                    u'status': u'OK',
                    u'cidr': u'172.21.0.0/16',
                    u'id': u'742cef84-512c-43fb-a469-8e9e87e35459',
                    u'name': u'VPC_2015-10-21-11-30-28'
                }
            },
            u'status': 200
        }
        """
        uri = "/v1/%s/vpcs/%s" % (project_id, vpc_id)
        return self.get(uri)

    def list_subnet(self, project_id, opts=None):
        """

        :param project_id: string
        :param opts: dict
        :return: dict
        {
            u'body': {
                u'subnets': [{
                    u'status': u'ACTIVE',
                    u'name': u'Subnet1',
                    u'dhcp_enable': True,
                    u'availability_zone': u'cn-north-1a',
                    u'primary_dns': u'114.114.114.114',
                    u'gateway_ip': u'172.21.0.1',
                    u'vpc_id': u'742cef84-512c-43fb-a469-8e9e87e35459',
                    u'cidr': u'172.21.0.0/24',
                    u'secondary_dns': u'114.114.115.115',
                    u'id': u'7bd9410f-38bb-4fbb-aa7a-cf4a22cb20f3'
                },
                {
                    u'status': u'ACTIVE',
                    u'name': u'subnet3',
                    u'dhcp_enable': True,
                    u'availability_zone': u'cn-north-1a',
                    u'primary_dns': u'114.114.114.114',
                    u'gateway_ip': u'172.21.2.1',
                    u'vpc_id': u'742cef84-512c-43fb-a469-8e9e87e35459',
                    u'cidr': u'172.21.2.0/24',
                    u'secondary_dns': u'114.114.115.115',
                    u'id': u'9fd27cfd-a988-4495-ae7c-c5521d8a5c09'
                },
                {
                    u'status': u'ACTIVE',
                    u'name': u'Subnet2',
                    u'dhcp_enable': True,
                    u'availability_zone': u'cn-north-1a',
                    u'primary_dns': u'114.114.114.114',
                    u'gateway_ip': u'172.21.1.1',
                    u'vpc_id': u'742cef84-512c-43fb-a469-8e9e87e35459',
                    u'cidr': u'172.21.1.0/24',
                    u'secondary_dns': u'114.114.115.115',
                    u'id': u'd654fe9f-0edc-42f0-a52b-f8c4cb8ac1da'
                }]
            },
            u'status': 200
        }
        """
        uri = "/v1/%s/subnets" % project_id
        if opts:
            str_opts = self.convertDictOptsToString(opts)
            uri = '?'.join([uri, str_opts])
        return self.get(uri)

    def list_subnet_detail(self, project_id, subnet_id):
        """

        :param project_id: string
        :param subnet_id: string
        :return: dict
        {
            u'body': {
                u'subnet': {
                    u'status': u'ACTIVE',
                    u'name': u'Subnet1',
                    u'dhcp_enable': True,
                    u'availability_zone': u'cn-north-1a',
                    u'primary_dns': u'114.114.114.114',
                    u'gateway_ip': u'172.21.0.1',
                    u'vpc_id': u'742cef84-512c-43fb-a469-8e9e87e35459',
                    u'cidr': u'172.21.0.0/24',
                    u'secondary_dns': u'114.114.115.115',
                    u'id': u'7bd9410f-38bb-4fbb-aa7a-cf4a22cb20f3'
                }
            },
            u'status': 200
        }
        """
        uri = "/v1/%s/subnets/%s" % (project_id, subnet_id)
        return self.get(uri)

    def create_subnet(self, project_id, name, cidr, availability_zone, vpc_id,
                      gateway_ip=None, dhcp_enable=None, primary_dns=None, secondary_dns=None):
        """

        :param project_id: string
        :param name: string
        :param cidr: string, '172.21.0.0/24'
        :param availability_zone: string, 'cn-north-1a'
        :param vpc_id: string
        :param gateway_ip: string
        :param dhcp_enable: string
        :param primary_dns: string
        :param secondary_dns: string
        :return:
        """
        uri = "/v1/%s/subnets" % project_id
        request_body_dict = {}
        subnet_map = {}
        subnet_map["name"] = name
        subnet_map["cidr"] = cidr
        subnet_map["availability_zone"] = availability_zone
        subnet_map["vpc_id"] = vpc_id
        if gateway_ip:
            subnet_map["gateway_ip"] = gateway_ip
        if dhcp_enable:
            subnet_map["dhcp_enable"] = dhcp_enable
        if primary_dns:
            subnet_map["primary_dns"] = primary_dns
        if secondary_dns:
            subnet_map["secondary_dns"] = secondary_dns
        request_body_dict["subnet"] = subnet_map

        request_body_string = json.dumps(request_body_dict)

        return self.post(uri, request_body_string)



