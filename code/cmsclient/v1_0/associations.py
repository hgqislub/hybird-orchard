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
Association interface.
"""

from oslo.utils import strutils
from six.moves.urllib import parse

from cmsclient import base
from cmsclient import exceptions
from cmsclient.i18n import _
from cmsclient import utils


class Association(base.Resource):
    """
    A association is an available hardware configuration for a server.
    """
    HUMAN_ID = True

    def __repr__(self):
        return "<Association: %s>" % self.name

    def delete(self):
        """
        Delete this association.
        """
        self.manager.delete(self)


class AssociationManager(base.ManagerWithFind):
    """
    Manage :class:`Association` resources.
    """
    resource_class = Association
    is_alphanum_id_allowed = True
    filter_items = ( "h%(name)s", "%(name)s", "userid" )

    def set_cloud(self, cloud):
        self.cloud = cloud
        self.prefix = "/%s" % base.getid(cloud)

    def list(self):
        """
        Get a list of all associations.

        :rtype: list of :class:`Association`.
        """

        return self._list(self.prefix + "/%s_association" % self.name, "associations")

    def get(self, association):
        """
        Get a specific association.

        :param association: The ID of the :class:`Association` to get.
        :rtype: :class:`Association`
        """
        return self._get(self.prefix + "/%s_association/%s" % (self.name, base.getid(association)), "association")

    def delete(self, association):
        """
        Delete a specific association.

        :param association: The ID of the :class:`Association` to get.
        """
        self._delete(self.prefix + "/%s_association/%s" % (self.name, base.getid(association)))

    def _build_body(self, **info):
        body = {}
        for k, v in info.items():
            if v is not None and k in [i % {'name': self.name} for i in self.filter_items]:
                body[k] = v

        return body and { "association": body }

    def update(self, id, **info):
        body = self._build_body(**info)
        if not body:
            return
        return self._update(self.prefix + "/%s_association/%s" % (self.name, id), body, "association")


    def create(self, **info):
        """
        Create a association.

        :param name: Descriptive name of the association
        :rtype: :class:`Association`
        """

        body = self._build_body(**info)

        return self._create(self.prefix + "/%s_association" % self.name, body, "association")

    def set_name(self, name):
        self.name = name
