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

    def create_vpc(self, project_id, name, cidr):
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

        request_body_dict = {}
        vpc_map = dict()
        vpc_map["name"] = name
        vpc_map["cidr"] = cidr

        request_body_dict["vpc"] = vpc_map
        request_body_string = json.dumps(request_body_dict)

        return self.post(uri, request_body_string)

    def delete_vpc(self, project_id, vpc_id):
        """
        :param project_id: string
        :param vpc_id: string
        :return: dict
        {
            u'status': 204
        }
        """
        uri = "/v1/%s/vpcs/%s" % (project_id, vpc_id)
        return self.delete(uri)

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
        subnet_map = dict()
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


    def delete_subnet(self, project_id, vpc_id, subnet_id):
        """
        :param project_id: string
        :param vpc_id: string
        :param subnet_id: string
        :return: dict
        {
            u'status': 204
        }
        """
        uri = "/v1/%s/vpcs/%s/subnets/%s" % (project_id, vpc_id, subnet_id)
        return self.delete(uri)

    def list_public_ips(self, project_id, opts=None):
        """
        :param project_id: string
        :param opts: dict
        :return: dict
        {
            u'status': 200
            "body"{
                "publicips": [
                {
                    "id": "6285e7be-fd9f-497c-bc2d-dd0bdea6efe0",
                    "status": "DOWN",
                    "type": "5_bgp",
                    "public_ip_address": "161.17.101.9",
                    "private_ip_address": "192.168.10.5",
                    "tenant_id": "8b7e35ad379141fc9df3e178bd64f55c",
                    "create_time": "2015-07-16 04:22:32",
                    "bandwidth_id": "3fa5b383-5a73-4dcb-a314-c6128546d855",
                    "bandwidth_share_type": "PER",
                    "bandwidth_size": 5
                },
                {
                    "id": "80d5b82e-43b9-4f82-809a-37bec5793bd4",
                    "status": "DOWN",
                    "type": "5_bgp",
                    "public_ip_address": "161.17.101.10",
                    "private_ip_address": "192.168.10.6",
                    "tenant_id": "8b7e35ad379141fc9df3e178bd64f55c",
                    "create_time": "2015-07-16 04:23:03",
                    "bandwidth_id": "a79fd11a-047b-4f5b-8f12-99c178cc780a",
                    "bandwidth_share_type": "PER",
                    "bandwidth_size": 5
                }
                ]
            }
        }
        """
        uri = "/v1/%s/publicips" % project_id
        if opts:
            str_opts = self.convertDictOptsToString(opts)
            uri = '?'.join([uri, str_opts])
        return self.get(uri)

    def create_public_ip(self, project_id, public_ip, bandwidth):
        """
        :param project_id: string
        :param public_ip: dict
        :param bandwidth: dict
        :return: dict
        {
            "body"{
                "publicip": {
                    "id": "f588ccfa-8750-4d7c-bf5d-2ede24414706",
                    "status": "PENDING_CREATE",
                    "type": "5_bgp",
                    "public_ip_address": "161.17.101.7",
                    "tenant_id": "8b7e35ad379141fc9df3e178bd64f55c",
                    "create_time": "2015-07-16 04:10:52",
                    "bandwidth_size": 0
                }
            }
            "status" : 200
        }
        """
        uri = "/v1/%s/publicips" % project_id

        request_body_dict = dict()

        request_body_dict["public_ip"] = public_ip
        request_body_dict["bandwidth"] = bandwidth
        request_body_string = json.dumps(request_body_dict)

        return self.post(uri, request_body_string)

    def delete_public_ip(self, project_id, public_ip_id):
        """
        :param project_id: string
        :param public_ip_id: string
        :return: dict
        {
            "status" : 204
        }
        """
        uri = "/v1/%s/publicips/%s" % (project_id, public_ip_id)
        return self.delete(uri)