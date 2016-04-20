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
User interface.
"""

from oslo.utils import strutils
from six.moves.urllib import parse

from cmsclient import base
from cmsclient import exceptions
from cmsclient.i18n import _
from cmsclient import utils


class User(base.Resource):
    """
    A user is an available hardware configuration for a server.
    """
    HUMAN_ID = True

    def __repr__(self):
        return "<User: %s>" % self.name

    def delete(self):
        """
        Delete this user.
        """
        self.manager.delete(self)


class UserManager(base.ManagerWithFind):
    """
    Manage :class:`User` resources.
    """
    resource_class = User
    is_alphanum_id_allowed = True
    filter_items = ( "name", "password", "region", "description" )
    

    def set_cloud(self, cloud):
        self.cloud = cloud
        self.prefix = "/%s" % base.getid(cloud)

    def list(self):
        """
        Get a list of all users.

        :rtype: list of :class:`User`.
        """
        return self._list(self.prefix + "/users", "users")

    def get(self, user):
        """
        Get a specific user.

        :param user: The ID of the :class:`User` to get.
        :rtype: :class:`User`
        """
        return self._get(self.prefix + "/users/%s" % base.getid(user), "user")

    def delete(self, user):
        """
        Delete a specific user.

        :param user: The ID of the :class:`User` to get.
        """
        self._delete(self.prefix + "/users/%s" % base.getid(user))

    def _build_body(self, **info):
        body = {}
        for k, v in info.items():
            if v is not None and k in self.filter_items:
                body[k] = v
        return body and { "user": body }

    def update(self, userid, **info):
        body = self._build_body(**info)
        if not body:
            return
        return self._update(self.prefix + "/users/%s" % userid, body, "user")


    def create(self, **info):
        """
        Create a user.

        :rtype: :class:`User`
        """

        body = self._build_body(**info)

        return self._create(self.prefix + "/users", body, "user")
