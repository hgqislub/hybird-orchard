__author__ = 'Administrator'

import json

from hwcloud.hws_service import HWSService

class EVSService(HWSService):
    def __init__(self, ak, sk, region, protocol, host, port):
        super(EVSService, self).__init__(ak, sk, 'EVS', region, protocol, host, port)

    def list(self, project_id, opts=None):
        uri = '/v2/%s/cloudvolumes' % project_id
        if opts:
            str_opts = self.convertDictOptsToString(opts)
            uri = '?'.join([uri, str_opts])

        return self.get(uri)

    def create_volume(self, project_id, availability_zone, size, volume_type,
                      backup_id=None, description=None, name=None, imageRef=None, count=None):
        """
        {
            "volume": {
                "backup_id": null,
                "count": 1,
                "availability_zone": "az1.dc1",
                "description": "test_volume_1",
                "size": 120,
                "name": "test_volume_1",
                "imageRef": null,
                "volume_type": "SSD"
            }
        }
        :param project_id:
        :param availability_zone:
        :param size:
        :param volume_type:
        :param backup_id:
        :param description:
        :param name:
        :param imageRef:
        :param count:
        :return: dict
        {
            "job_id": "70a599e0-31e7-49b7-b260-868f441e862b",
        }
        or
        {
            "error": {
                "message": "XXXX",
                "code": "XXX"
            }
        }
        Get job detail result:
        {
            u'body': {
                u'status': u'RUNNING',
                u'fail_reason': None,
                u'job_id': u'8aace0c651b0a02301521ae1f96c6138',
                u'job_type': u'createVolume',
                u'entities': {
                    u'volume_id': u'9bd6fa88-0e60-48e5-ae61-7e028dbdf045'
                },
                u'end_time': u'',
                u'begin_time': u'2016-01-07T06: 59: 23.115Z',
                u'error_code': None
            },
            u'status': 200
        }
        {
            u'body': {
                u'status': u'SUCCESS',
                u'fail_reason': None,
                u'job_id': u'8aace0c651b0a02301521ae1f96c6138',
                u'job_type': u'createVolume',
                u'entities': {
                    u'volume_id': u'9bd6fa88-0e60-48e5-ae61-7e028dbdf045'
                },
                u'end_time': u'2016-01-07T06: 59: 48.279Z',
                u'begin_time': u'2016-01-07T06: 59: 23.115Z',
                u'error_code': None
            },
            u'status': 200
        }

        Failed job result:
        {
            u'body': {
                u'status': u'FAIL',
                u'fail_reason': u"EbsCreateVolumeTask-fail:badRequest: Invalid input received: Availability zone 'cn-north-1' is invalid",
                u'job_id': u'8aace0c651b0a02301521ab7e58660ca',
                u'job_type': u'createVolume',
                u'entities': {

                },
                u'end_time': u'2016-01-07T06: 13: 25.809Z',
                u'begin_time': u'2016-01-07T06: 13: 25.509Z',
                u'error_code': u'EVS.5400'
            },
            u'status': 200
        }

        """
        uri = '/v2/%s/cloudvolumes' % project_id
        request_body_dict = {}
        volume = {}
        volume['availability_zone'] = availability_zone
        volume['size'] = size
        volume['volume_type'] = volume_type

        if backup_id:
            volume['backup_id'] = backup_id

        if description:
            volume['description'] = description

        if name:
            volume['name'] = name

        if imageRef:
            volume['imageRef'] = imageRef

        if count:
            volume['count'] = count

        request_body_dict['volume'] = volume
        request_body_string = json.dumps(request_body_dict)

        response = self.post(uri, request_body_string)

        return response

    def delete_volume(self, project_id, volume_id):
        """
        DELETE /v2/{tenant_id}/cloudvolumes/{volume_id}

        :return:
        """
        uri = '/v2/%s/cloudvolumes/%s' % (project_id, volume_id)
        response = self.delete(uri)

        return response

    def get_volume_detail(self, project_id, volume_id):
        uri = "/v2/%s/volumes/%s" % (project_id, volume_id)

        response = self.get(uri)

        return response