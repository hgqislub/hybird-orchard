__author__ = 'Administrator'

import json

from hwcloud.hws_service import HWSService


class VBSService(HWSService):
    def __init__(self, ak, sk, region, protocol, host, port):
        super(VBSService, self).__init__(ak, sk, 'VPC', region, protocol, host, port)

    def create_backup(self, project_id, volume_id, name=None, description=None):
        """
        job create response:
        {
            'body':
                {
                    'job_id': ''
                },
            'status': 200
        }

        get job detail response:
        {
            'body':
                {
                    'status': 'FAIL',
                    'fail_reason': 'CreateBackup Task-fail: fsp cinder return backup status is error.'
                    'job_id': '4010b39b523388bb015252460a581a3d',
                    'job_type': 'bksCreateBackup',
                    'entities':
                        {
                            'bks_create_volume_name': 'autobk_volume_2016-01-15T01:0807.476Z',
                            'backup_id': '',
                            'snapshot_id': 'faddfasdf',
                            'volume_id': 'safdafadf'
                        },
                    'end_time': '2016-01-15T01:0807.476Z',
                    'begin_time': '2016-01-15T01:0807.476Z',
                    'error_code': 'VolumeBackup.0064'
                },
            'status': 200
        }

        :param project_id:
        :param volume_id:
        :param name:
        :param description:
        :return:
        """
        uri = '/v2/%s/cloudbackups' % project_id
        request_body = {}
        backup = {}
        backup['volume_id'] = volume_id
        if name:
            backup['name'] = name
        if description:
            backup['description'] = description
        request_body['backup'] = backup
        request_body_string = json.dumps(request_body)
        response = self.post(uri, request_body_string)

        return response

    def delete_backup(self, project_id, backup_id):
        uri = '/v2/%s/cloudbackups/%s' % (project_id, backup_id)
        response = self.delete(uri)

        return response

