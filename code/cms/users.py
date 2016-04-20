import webob
from cms import exception
from cms import wsgi
from cms import db
from cms.clouds import check_cloud_first

from cms.views import users as users_view

class UserController(wsgi.Application):
    _view_builder = users_view.ViewBuilder()
    
    @check_cloud_first
    def list(self, request, client, region, **kwargs):
        result = client.users.findall(region=region)
        return self._view_builder.detail(request, result)

    @check_cloud_first
    def get_user(self, request, user_id, client, region, client_exc, **kwargs):
        try:
            result = client.users.get(user_id)
        except client_exc.NotFound:
            result = client.users.find(region=region, id=user_id)

        if result.region != region:
            raise exception.UserNotFound(id=user_id)

        return self._view_builder.show(request, result)

    @check_cloud_first
    def create_user(self, request, user, 
                      client, region, client_exc, **kwargs):
        user['region'] = region
        result = client.users.create(**user)
        return self._view_builder.show(request, result)

    @check_cloud_first
    def update_user(self, request, user_id, user, 
                      client, region, client_exc, **kwargs):
        try:
            result = client.users.get(user_id)
        except client_exc.NotFound:
            result = client.users.find(region=region, id=user_id)

        if result.region != region:
            raise exception.UserNotFound(id=user_id)

        result = client.users.update(user_id, **user)
        return self._view_builder.show(request, result)

    @check_cloud_first
    def delete_user(self, request, user_id, 
                      client, region, client_exc, **kwargs):
        try:
            result = client.users.get(user_id)
        except client_exc.NotFound:
            result = client.users.find(region=region, id=user_id)

        if result.region != region:
            raise exception.UserNotFound(id=user_id)

        client.users.delete(user_id)
        return webob.Response(status_int=204)

def create_router(mapper):
    user_controller = UserController()
    mapper.connect('/{cloud_id}/users',
                   controller=user_controller,
                   action='list',
                   conditions=dict(method=['GET']))
    mapper.connect('/{cloud_id}/users',
                   controller=user_controller,
                   action='create_user',
                   conditions=dict(method=['POST']))
    mapper.connect('/{cloud_id}/users/{user_id}',
                   controller=user_controller,
                   action='get_user',
                   conditions=dict(method=['GET']))
    mapper.connect('/{cloud_id}/users/{user_id}',
                   controller=user_controller,
                   action='update_user',
                   conditions=dict(method=['PUT']))
    mapper.connect('/{cloud_id}/users/{user_id}',
                   controller=user_controller,
                   action='delete_user',
                   conditions=dict(method=['DELETE']))

