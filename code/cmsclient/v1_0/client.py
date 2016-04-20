# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

from cmsclient import client
from cmsclient.v1_0 import certs
from cmsclient.v1_0 import users
from cmsclient.v1_0 import clouds
from cmsclient.v1_0 import associations
from cmsclient.v1_0 import versions


class Client(object):
    """
    Top-level object to access the OpenStack Compute API.

    Create an instance with your creds::

        >>> client = Client(USERNAME, PASSWORD, PROJECT_ID, AUTH_URL)

    Or, alternatively, you can create a client instance using the
    keystoneclient.session API::

        >>> from keystoneclient.auth.identity import v2
        >>> from keystoneclient import session
        >>> from cmsclient.client import Client
        >>> auth = v2.Password(auth_url=AUTH_URL,
                               username=USERNAME,
                               password=PASSWORD,
                               tenant_name=PROJECT_ID)
        >>> sess = session.Session(auth=auth)
        >>> nova = client.Client(VERSION, session=sess)

    Then call methods on its managers::

        >>> client.servers.list()
        ...
        >>> client.users.list()
        ...

    It is also possible to use an instance as a context manager in which
    case there will be a session kept alive for the duration of the with
    statement::

        >>> with Client(USERNAME, PASSWORD, PROJECT_ID, AUTH_URL) as client:
        ...     client.servers.list()
        ...     client.users.list()
        ...

    It is also possible to have a permanent (process-long) connection pool,
    by passing a connection_pool=True::

        >>> client = Client(USERNAME, PASSWORD, PROJECT_ID,
        ...     AUTH_URL, connection_pool=True)
    """

    def __init__(self, username=None, api_key=None, project_id=None,
                 auth_url=None, insecure=False, timeout=None,
                 endpoint_type='publicURL', 
                  timings=False, bypass_url=None,
                 os_cache=False, no_cache=True, http_log_debug=False,
                 auth_system='keystone', auth_plugin=None, auth_token=None,
                 cacert=None, tenant_id=None, user_id=None,
                 connection_pool=False, session=None, auth=None,
                 completion_cache=None):
        # FIXME(comstud): Rename the api_key argument above when we
        # know it's not being used as keyword argument

        # NOTE(cyeoh): In the cmsclient context (unlike Nova) the
        # project_id is not the same as the tenant_id. Here project_id
        # is a name (what the Nova API often refers to as a project or
        # tenant name) and tenant_id is a UUID (what the Nova API
        # often refers to as a project_id or tenant_id).

        password = api_key
        self.user_id = user_id
        self.clouds = clouds.CloudManager(self)
        self.users = users.UserManager(self)
        self.associations = associations.AssociationManager(self)
        self.versions = versions.VersionManager(self)

        self.client = client._construct_http_client(
            username=username,
            password=password,
            user_id=user_id,
            auth_url=auth_url,
            auth_token=auth_token,
            insecure=insecure,
            timeout=timeout,
            auth_system=auth_system,
            auth_plugin=auth_plugin,
            timings=timings,
            bypass_url=bypass_url,
            os_cache=os_cache,
            http_log_debug=http_log_debug,
            cacert=cacert,
            connection_pool=connection_pool,
            session=session,
            auth=auth)

        self.completion_cache = completion_cache

    def write_object_to_completion_cache(self, obj):
        if self.completion_cache:
            self.completion_cache.write_object(obj)

    def clear_completion_cache_for_class(self, obj_class):
        if self.completion_cache:
            self.completion_cache.clear_class(obj_class)

    @client._original_only
    def __enter__(self):
        self.client.open_session()
        return self

    @client._original_only
    def __exit__(self, t, v, tb):
        self.client.close_session()

    @client._original_only
    def set_management_url(self, url):
        self.client.set_management_url(url)

    @client._original_only
    def get_timings(self):
        return self.client.get_timings()

    @client._original_only
    def reset_timings(self):
        self.client.reset_timings()

    @client._original_only
    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()
