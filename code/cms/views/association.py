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

    def __init__(self, name):
        self.fields = ["id", "h" + name, name, "region"]
        if name == 'project':
            self.fields.append('userid')

    def basic(self, request, assoc):
        return {
            "association": {
                "id": assoc.id,
            },
        }

    def show(self, request, assoc):
        obj =  {}
        for f in self.fields:
            obj[f] = getattr(assoc, f)
        return  {"association":  obj}

    def index(self, request, associations):
        """Return the 'index' view of associations."""
        return self._list_view(self.basic, request, associations)

    def detail(self, request, associations):
        """Return the 'detail' view of associations."""
        return self._list_view(self.show, request, associations)

    def _list_view(self, func, request, associations):
        """Provide a view for a list of association."""
        return dict(associations=[func(request, assoc)["association"] for assoc in associations])

