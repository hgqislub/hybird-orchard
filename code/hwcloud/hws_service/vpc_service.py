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

    def create_subnet(self, project_id, name, cidr, availability_zone,gateway_ip, vpc_id,
                      dhcp_enable=None, primary_dns=None, secondary_dns=None):
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

        request_body_dict["publicip"] = public_ip
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

    def list_security_groups(self, project_id, opts=None):
        """
        :param project_id: string
        :param opts: dict
        :return: dict
        {
            "security_groups": [
                {
                    "id": "16b6e77a-08fa-42c7-aa8b-106c048884e6",
                    "name": "qq",
                    "vpc_id": "3ec3b33f-ac1c-4630-ad1c-7dba1ed79d85",
                    "security_group_rules": [
                        {
                            "direction": "egress",
                            "ethertype": "IPv4",
                            "id": "369e6499-b2cb-4126-972a-97e589692c62",
                            "security_group_id": "16b6e77a-08fa-42c7-aa8b-106c048884e6"
                        },
                        {
                            "direction": "ingress",
                            "ethertype": "IPv4",
                            "id": "0222556c-6556-40ad-8aac-9fd5d3c06171",
                            "remote_group_id": "16b6e77a-08fa-42c7-aa8b-106c048884e6",
                            "security_group_id": "16b6e77a-08fa-42c7-aa8b-106c048884e6"
                        }
                    ]
                },
                {
                    "id": "9c0f56be-a9ac-438c-8c57-fce62de19419",
                    "name": "default",
                    "vpc_id": "13551d6b-755d-4757-b956-536f674975c0",
                    "security_group_rules": [
                        {
                            "direction": "egress",
                            "ethertype": "IPv4",
                            "id": "95479e0a-e312-4844-b53d-a5e4541b783f",
                            "security_group_id": "9c0f56be-a9ac-438c-8c57-fce62de19419"
                        },
                        {
                            "direction": "ingress",
                            "ethertype": "IPv4",
                            "id": "0c4a2336-b036-4fa2-bc3c-1a291ed4c431",
                            "remote_group_id": "9c0f56be-a9ac-438c-8c57-fce62de19419",
                            "security_group_id": "9c0f56be-a9ac-438c-8c57-fce62de19419"
                        }
                    ]
                }
            ]
        }
        """

        uri = "/v1/%s/security-groups" % project_id
        if opts:
            str_opts = self.convertDictOptsToString(opts)
            uri = '?'.join([uri, str_opts])
        return self.get(uri)

    def create_security_group_rule(self, project_id, security_group_id, direction,
                                ethertype, protocol=None, port_range_min=None,
                                port_range_max = None, remote_ip_prefix = None,
                                remote_group_id = None):
        """

        :param project_id:
        :param security_group_id:
        :param direction:
        :param ethertype:
        :param protocol:
        :param port_range_min:
        :param port_range_max:
        :param remote_ip_prefix:
        :param remote_group_id:
        :return:
        {
            "security_group_rule":{
                "direction":"ingress",
                "ethertype":"IPv4",
                "id":"2bc0accf-312e-429a-956e-e4407625eb62",
                "port_range_max":80,
                "port_range_min":80,
                "protocol":"tcp",
                "remote_group_id":"85cc3048-abc3-43cc-89b3-377341426ac5",
                "remote_ip_prefix":null,
                "security_group_id":"a7734e61-b545-452d-a3cd-0189cbd9747a",
                "tenant_id":"e4f50856753b4dc6afee5fa6b9b6c550"
            }
        }
        """
        uri = "/v1/%s/security-group-rules" % project_id

        request_body_dict = dict()
        security_group_rule = dict()
        security_group_rule["security_group_id"] = security_group_id
        security_group_rule["direction"] = direction
        security_group_rule["ethertype"] = ethertype
        if protocol:
            security_group_rule["protocol"] = protocol
        if port_range_min:
            security_group_rule["port_range_min"] = port_range_min
        if port_range_max:
            security_group_rule["port_range_max"] = port_range_max
        if remote_ip_prefix:
            security_group_rule["remote_ip_prefix"] = remote_ip_prefix
        if remote_group_id:
            security_group_rule["remote_group_id"] = remote_group_id

        request_body_dict["security_group_rule"] = security_group_rule
        request_body_string = json.dumps(request_body_dict)

        return self.post(uri, request_body_string)

    def list_server_nics(self, project_id, server_id):
        """
        :param project_id:
        :param server_id:
        :return:
        {
            "interfaceAttachments": [
                {
                    "port_state": "ACTIVE",
                    "fixed_ips": [
                        {
                            "subnet_id": "f8a6e8f8-c2ec-497c-9f23-da9616de54ef",
                            "ip_address": "192.168.1.3"
                        }
                    ],
                    "net_id": "3cb9bc59-5699-4588-a4b1-b87f96708bc6",
                    "port_id": "ce531f90-199f-48c0-816c-13e38010b442",
                    "mac_addr": "fa:16:3e:4c:2c:30"
                }
            ]
        }
        """
        uri = "/v2/%s/servers/%s/os-interface" % (project_id, server_id)
        return self.get(uri)

    def bind_public_ip(self, project_id, public_ip_id, port_id):
        """
        :param project_id:
        :param public_id:
        :param port_id:
        :return:
        {
            "publicip": {
                "id": "f588ccfa-8750-4d7c-bf5d-2ede24414706",
                "status": "PENDING_UPDATE",
                "type": "5_bgp",
                "public_ip_address": "161.17.101.7",
                "port_id": "f588ccfa-8750-4d7c-bf5d-2ede24414706",
                "tenant_id": "8b7e35ad379141fc9df3e178bd64f55c",
                "create_time": "2015-07-16 04:10:52",
                "bandwidth_size": 6
            }
        }
        """
        uri = "/v1/%s/publicips/%s" % (project_id, public_ip_id)
        request_body_dict = dict()
        publicip = dict()
        publicip["port_id"] = port_id
        request_body_dict["publicip"] = publicip
        request_body_string = json.dumps(request_body_dict)
        return self.put(uri, request_body_string)
