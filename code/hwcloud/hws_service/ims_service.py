__author__ = 'Administrator'

import json

from hwcloud.hws_service import HWSService


class IMSService(HWSService):
    def __init__(self, ak, sk, region, protocol, host, port):
        super(IMSService, self).__init__(ak, sk, 'IMS', region, protocol, host, port)

    def list(self, project_id):
        uri = '/v2/images'
        return self.get(uri)

    def create_image(self, name, description, instance_id=None, backup_id=None):
        """
        POST /v2/cloudimages/action
        Request Body:
        {
        "name":"ims_test",
        "description":"xxxxx",
        "instance_id":"877a2cda-ba63-4e1e-b95f-e67e48b6129a"
        }

        Request Body:
        {
        "name":"ims_test",
        "description":"xxxxx",
        "backup_id":"f5bb2392-db73-4986-8aed-9623a1474b2c"
        }
        :param project_id:
        :return:
        """
        uri = '/v2/cloudimages/action'
        request_body_dict = {}
        request_body_dict['name'] = name
        request_body_dict['description'] = description
        if instance_id:
            request_body_dict['instance_id'] = instance_id
        if backup_id:
            request_body_dict['backup_id'] = backup_id
        request_body_string = json.dumps(request_body_dict)

        response = self.post(uri, request_body_string)

        return response

    def delete_image(self, image_id):
        uri = '/v2/images/%s' % image_id
        response = self.delete(uri)

        return response