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

    _collection_name = "users"

    def basic(self, request, user):
        return {
            "user": {
                "id": user.id,
            },
        }

    def show(self, request, user):
        user_dict = {
            "user": {
                "id": user.id,
                "name": user.name,
                "region": user.region,
                "description": getattr(user, "description", ""),
            }
        }

        return user_dict

    def index(self, request, users):
        """Return the 'index' view of users."""
        return self._list_view(self.basic, request, users)

    def detail(self, request, users):
        """Return the 'detail' view of users."""
        return self._list_view(self.show, request, users)

    def _list_view(self, func, request, users):
        """Provide a view for a list of users."""
        user_list = [func(request, user)["user"] for user in users]
        users_dict = dict(users=user_list)

        return users_dict

