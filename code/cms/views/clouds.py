# Copyright 2010-2011 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


class ViewBuilder(object):

    _collection_name = "clouds"

    def basic(self, request, cloud):
        return {
            "cloud": {
                "id": cloud["uuid"],
            },
        }

    def show(self, request, cloud):
        cloud_type = cloud['cloud_type'].lower()
        if cloud_type == 'fusionsphere':
            cloud_type = 'openstack'
        template_cloud = {
            "aws": {
                "availability_zone": None,
                "region": None,
                "cloud_type": None,
                "cloud_info": {
                    "aws_availabilityzone": None,
                    "accesskey": None,
                    "secretkey": None,
                }
            },
            "vcloud": {
                "availability_zone": None,
                "region": None,
                "cloud_type": None,
                "cloud_info": {
                    "vpninfo": {
                        "public_ip": None,
                        "api_ip": None,
                        "api_subnet": None,
                        "data_ip": None,
                        "data_subnet": None,
                    },
                    "vCloud_info": {
                        "org": None,
                        "vdc": None,
                        "username": None,
                        "password": None,
                        "external_id": None
                    }
                }
            },
            "openstack": {
                "availability_zone": None,
                "region": None,
                "cloud_type": None,
                "cloud_info": {
                    "vpninfo": {
                        "public_ip": None,
                        "api_ip": None,
                        "api_subnet": None,
                        "data_ip": None,
                        "data_subnet": None,
                    },
                    "cloud_urlinfo": {
                        "domainname":None
                    }
                }
            }
        }.get(cloud_type)

        new_cloud = {}

        def _fill_none_fields(template, new_cloud):
            
            for k, v in template.items():
                if v is None:
                    if cloud.get(k):
                        new_cloud[k] = cloud[k]
                if type(v) is dict:
                    new_cloud[k] = {}
                    _fill_none_fields(v, new_cloud[k])

        if 'uuid' in cloud:
            new_cloud['id'] = cloud['uuid']
        if template_cloud:
            _fill_none_fields(template_cloud, new_cloud)

        return { "cloud": new_cloud }

    def index(self, request, clouds):
        """Return the 'index' view of clouds."""
        return self._list_view(self.basic, request, clouds)

    def detail(self, request, clouds):
        """Return the 'detail' view of clouds."""
        return self._list_view(self.show, request, clouds)

    def _list_view(self, func, request, clouds):
        """Provide a view for a list of clouds."""
        cloud_list = [func(request, cloud)["cloud"] for cloud in clouds]
        clouds_dict = dict(clouds=cloud_list)

        return clouds_dict

