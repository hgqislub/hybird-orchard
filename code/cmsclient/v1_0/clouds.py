# Copyright 2010 Jacob Kaplan-Moss
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

"""
Cloud interface.
"""

from oslo.utils import strutils
from six.moves.urllib import parse

from cmsclient import base
from cmsclient import exceptions
from cmsclient.i18n import _
from cmsclient import utils

# cloud field
required_common_fields = ["cloud_type", "availability_zone", "region"]

vpn_info = ["public_ip", "api_ip", "api_subnet", "data_ip", "data_subnet"]
cloud_urlinfo = ["domainname"]
vcloud_info = ["org", "vdc", "username", "password", "external_id"]
aws_info = ["aws_availabilityzone", "accesskey", "secretkey"]

required_other_fields = {
        "vcloud" :  vpn_info + vcloud_info,
        "openstack": vpn_info + cloud_urlinfo,
        "fusionsphere": vpn_info + cloud_urlinfo,
        "aws": aws_info, 
}
all_fields = required_common_fields + vpn_info + vcloud_info + cloud_urlinfo + aws_info

class MissingArgs(Exception):
    """Supplied arguments are not sufficient for calling a function."""
    def __init__(self, missing):
        self.missing = missing
        msg = _("Missing arguments: %s") % ", ".join(missing)
        super(MissingArgs, self).__init__(msg)

class UnsupportCloudType(Exception):
    """Unsupported cloud type. """
    def __init__(self, cloud_type):
        self.cloud_type = cloud_type
        msg = _(("Unsupported cloud type %s. Only " + ','.join(required_other_fields.keys()) + " (case insensitive) are currently supported.") % cloud_type)
        super(UnsupportCloudType, self).__init__(msg)

class Cloud(base.Resource):
    """
    A cloud is an available hardware configuration for a server.
    """
    HUMAN_ID = True

    def __repr__(self):
        return "<Cloud: %s>" % self.name

    def delete(self):
        """
        Delete this cloud.
        """
        self.manager.delete(self)


class CloudManager(base.ManagerWithFind):
    """
    Manage :class:`Cloud` resources.
    """
    resource_class = Cloud
    is_alphanum_id_allowed = True

    def list(self):
        """
        Get a list of all clouds.

        :rtype: list of :class:`Cloud`.
        """
        return self._list("/clouds", "clouds")

    def get(self, cloud):
        """
        Get a specific cloud.

        :param cloud: The ID of the :class:`Cloud` to get.
        :rtype: :class:`Cloud`
        """
        return self._get("/clouds/%s" % base.getid(cloud), "cloud")

    def delete(self, cloud):
        """
        Delete a specific cloud.

        :param cloud: The ID of the :class:`Cloud` to get.
        """
        self._delete("/clouds/%s" % base.getid(cloud))

    def _build_body(self, **info):
        body = {}
        for k, v in info.items():
            if v is not None and k in all_fields:
                body[k] = v
        return body and { "cloud": body }

    def update(self, cloudid, **info):
        body = self._build_body(**info)
        if not body:
            return
        return self._update("/clouds/%s" % cloudid, body, "cloud")



    def create(self, **info):
        """
        Create a cloud.

        :rtype: :class:`Cloud`
        """

        missings = [ f for f in required_common_fields if info.get(f) is None]
        if missings:
            raise MissingArgs(missings)

        cloud_type = info["cloud_type"].lower()
        if cloud_type not in required_other_fields.keys():
            raise UnsupportCloudType(cloud_type)

        missings = [ f for f in required_other_fields[cloud_type] if info.get(f) is None]
        if missings:
            raise MissingArgs(missings)
    
        body = self._build_body(**info)

        return self._create("/clouds", body, "cloud")
