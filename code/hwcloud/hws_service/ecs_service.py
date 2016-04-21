__author__ = 'Administrator'

import json

from hwcloud.hws_service import HWSService


class ECSService(HWSService):
    def __init__(self, ak, sk, region, protocol, host, port):
        super(ECSService, self).__init__(ak, sk, 'ECS', region, protocol, host, port)

    def list(self, project_id, opts=None):
        """

        :param project_id: string
        :param opts: dict
        :return:
        {
            u'body': {
                u'servers': [{
                    u'id': u'817187bd-7691-408b-a78e-0bb0e8407cd6',
                    u'links': [{
                        u'href': u'https: //compute.region.cnnorth1.hwclouds.com/v2/91d957f0b92d48f0b184c26975d2346e/servers/817187bd-7691-408b-a78e-0bb0e8407cd6',
                        u'rel': u'self'
                    },
                    {
                        u'href': u'https: //compute.region.cnnorth1.hwclouds.com/91d957f0b92d48f0b184c26975d2346e/servers/817187bd-7691-408b-a78e-0bb0e8407cd6',
                        u'rel': u'bookmark'
                    }],
                    u'name': u's_server_01'
                }]
            },
            u'status': 200
        }
        """
        uri = "v2/%s/servers" % project_id
        if opts:
            str_opts = self.convertDictOptsToString(opts)
            uri = '?'.join([uri, str_opts])
        return self.get(uri)

    def list_detail(self, project_id, opts=None):
        uri = "/v2/%s/servers/detail" % project_id
        if opts:
            str_opts = self.convertDictOptsToString(opts)
            uri = '?'.join([uri, str_opts])
        return self.get(uri)

    def get_detail(self, project_id, server_id):
        """

        :param project_id:
        :param server_id:
        :return:
        """
        uri = '/v2/%s/servers/%s' % (project_id, server_id)
        return self.get(uri)

    def create_server(self, project_id, image_ref, flavor_ref, name, vpcid, nics_subnet_list, root_volume_type,
                      personality_path=None, personality_contents=None, adminPass=None, public_ip_id=None, count=None,
                      data_volumes=None, security_groups=None, availability_zone=None, key_name=None):
        """
        Rest method: POST
        Uri for create server: /v1/{project_id}/cloudservers
        Request body of create server in hws is as following:
        {
            "server": {
            "availability_zone": "az1.dc1",
            "name": "newserver",
            "imageRef": "imageid",
            "root_volume": {
                "volumetype": "SATA"
            },
            "data_volumes": [
                {
                    "volumetype": "SATA",
                    "size": 100
                },
                {
                    "volumetype": "SSD",
                    "size": 100
                }
            ],
            "flavorRef": " 1",
            "personality": [
                {
                    "path": "/etc/banner.txt",
                    "contents": "ICAgICAgDQoiQmFjaA=="
                }
            ],
            "vpcid": "vpcid",
            "security_groups": [
                {
                    "id": "securitygroupsid"
                }
            ],
            "nics": [
                {
                    "subnet_id": "subnetid "
                }
            ],
            "publicip": {
                "id": "publicipid"
            },
            "key_name": "keyname",
            "adminPass": "password",
            "count": 1
            }
        }

        :param project_id: string
        :param imageRef: string
        :param flavorRef: string
        :param name: string
        :param vpcid: string
        :param nics_subnet_list: list of subnet_id, ['subnet_id_01', 'subnet_id_02']
        :param root_volume_type: string
        :param personality_path: string
        :param personality_contents: string
        :param adminPass: string
        :param public_ip_id: string
        :param count: int
        :param data_volumes: list
            [
                {
                    "volumetype": "SATA",
                    "size": 100
                },
                {
                    "volumetype": "SSD",
                    "size": 100
                }
            ]
        :param security_groups: list of security group id, e.g. ['sg_id_01', 'sg_id_02']
        :param availability_zone: string
        :param key_name: string
        :return:
        {
            u'body': {
                u'job_id': u'8aace0c851b0a3c10151eca2b4183764'
            },
            u'status': 200
        }
        """
        uri = "/v1/%s/cloudservers" % project_id
        request_body_dict = {}

        request_server_body = {}
        request_server_body['imageRef'] = image_ref
        request_server_body['flavorRef'] = flavor_ref
        request_server_body['name'] = name
        request_server_body['vpcid'] = vpcid

        if adminPass:
            request_server_body['adminPass'] = adminPass

        if count:
            request_server_body['count'] = count

        if personality_path and personality_contents:
            personality = {}
            personality['path'] = personality_path
            personality['contents'] = personality_contents
            request_server_body['personality'] = personality

        if nics_subnet_list:
            nics_list = []
            for subnet_id in nics_subnet_list:
                subnet_dict = {}
                subnet_dict['subnet_id'] = subnet_id
                nics_list.append(subnet_dict)
            request_server_body['nics'] = nics_list

        if public_ip_id:
            public_ip_dict = {}
            public_ip_dict[id] = public_ip_id
            request_server_body['publicip'] = public_ip_dict

        if root_volume_type:
            root_volume_dict = {}
            root_volume_dict['volumetype'] = root_volume_type
            request_server_body['root_volume'] = root_volume_dict

        if data_volumes:
            request_server_body['data_volumes'] = data_volumes

        if security_groups:
            security_group_list = []
            for security_group_id in security_groups:
                security_group_dict = {}
                security_group_dict['id'] = security_group_id
                security_group_list.append(security_group_dict)
            request_server_body['security_groups'] = security_group_list

        if availability_zone:
            request_server_body['availability_zone'] = availability_zone

        if key_name:
            request_server_body['key_name'] = key_name


        request_body_dict['server'] = request_server_body
        request_body_string = json.dumps(request_body_dict)
        response = self.post(uri, request_body_string)

        return response

    def list_flavors(self, project_id):
        """

        :param project_id: string
        :return: dict
        {
            "body":{
                "flavors": [
                    {
                        "id": "104",
                        "name": "m1.large",
                        "vcpus": "4",
                        "ram": 8192,
                        "disk": "80",
                        "swap": "",
                        "OS-FLV-EXT-DATA:ephemeral": 0,
                        "rxtx_factor": null,
                        "OS-FLV-DISABLED:disabled": null,
                        "rxtx_quota": null,
                        "rxtx_cap": null,
                        "os-flavor-access:is_public": null,
                        "os_extra_specs": {
                            "hws:performancetype": "normal",
                            "hws:availablezone": "az1.dc1"
                        }
                    },
                ]
            },
            "status": 200
        }
        """
        uri =  "/v1/%s/cloudservers/flavors" % project_id
        return self.get(uri)

    def delete_server(self, project_id, server_id_list, delete_public_ip, delete_volume):
        """
        {
            "servers": [
                {
                    "id": "616fb98f-46ca-475e-917e-2563e5a8cd19"
                }
            ],
            "delete_publicip": False,
            "delete_volume": False
        }
        :param project_id: string, project id
        :param server_id_list: list, e.g. [server_id, ...]
        :param delete_public_ip: boolean
        :param delete_volume: boolean
        :return:
        """
        uri = "/v1/%s/cloudservers/delete" % project_id
        request_body_dict = {}

        server_dict_list = []
        for server_id in server_id_list:
            id_dict = {"id":server_id}
            server_dict_list.append(id_dict)
        request_body_dict["servers"] = server_dict_list
        request_body_dict["delete_publicip"] = delete_public_ip
        request_body_dict["delete_volume"] = delete_volume

        request_body_string = json.dumps(request_body_dict)
        response = self.post(uri, request_body_string)

        return response

    def stop_server(self, project_id, server_id):
        uri = '/v2/%s/servers/%s/action' % (project_id, server_id)
        request_body_dict = {}
        request_body_dict['os-stop'] = {}
        request_body_string = json.dumps(request_body_dict)
        response = self.post(uri, request_body_string)

        return response

    def stop_servers(self, project_id, servers_list):
        pass


    def start_server(self, project_id, server_id):
        uri = '/v2/%s/servers/%s/action' % (project_id, server_id)
        request_body_dict = {"os-start": {}}
        request_body_string = json.dumps(request_body_dict)
        response = self.post(uri, request_body_string)

        return response

    def reboot_hard(self, project_id, server_id):
        return self.reboot(project_id, server_id, "HARD")

    def reboot_soft(self, project_id, server_id):
        return self.reboot(project_id, server_id, "SOFT")

    def reboot(self, project_id, server_id, type):
        """

        :param project_id:
        :param server_id:
        :param type: string, "SOFT" or "HARD"
        :return:
        """
        uri = '/v2/%s/servers/%s/action' % (project_id, server_id)
        request_body_dict = {
                                "reboot": {
                                    "type": type
                                }
                            }
        request_body_string = json.dumps(request_body_dict)
        response = self.post(uri, request_body_string)

        return response

    def attach_volume(self, project_id, server_id, volume_id, device_name):
        uri = 'v1/%s/cloudservers/%s/attachvolume' % (project_id, server_id)
        request_body = {}
        volume_attachment = {}
        volume_attachment['volumeId'] = volume_id
        volume_attachment['device'] = device_name
        request_body['volumeAttachment'] = volume_attachment
        request_body_string = json.dumps(request_body)
        response = self.post(uri, request_body_string)

        return response

    def detach_volume(self, project_id, server_id, attachment_id):
        uri = '/v1/%s/cloudservers/%s/detachvolume/%s' % (project_id, server_id, attachment_id)
        response = self.delete(uri)

        return response

    def get_volume_list(self, project_id, server_id):
        uri = '/v2/%s/servers/%s/os-volume_attachments' % (project_id, server_id)
        response = self.get(uri)
        return response

