import webob
from cms import exception
from cms import wsgi
from cms import db
from cms.context import DEFAULT_ADMIN_CONTEXT as default_context
from cms.views import clouds as clouds_view
from cms.repoze_lru import LRUCache as lru

from oslo.config import cfg
import functools
import uuid

from fs_gatewayclient.client import Client as FSClient
from fs_gatewayclient import exceptions as FSClient_Exc

CONF = cfg.CONF

_clouds_cache = lru(1000)

def _gen_uuid():
    return unicode(uuid.uuid4())

def flattening_dict(old_cloud):
    new_cloud = {}
    def _flatten_dict(old):
        for k, v in old.items():
            if type(v) is dict:
                _flatten_dict(v)
            else:
                new_cloud[k] = v
    _flatten_dict(old_cloud)
    if 'id' in new_cloud:
        new_cloud['uuid'] = new_cloud.pop('id')
    return new_cloud


def _cloud_get(cloud_id):
    global _clouds_cache
    cloud = _clouds_cache.get(cloud_id)
    if cloud is None:
        try:
            cloud = db.cloud_get(default_context, cloud_id)
            _clouds_cache.put(cloud_id, cloud)
        except exception.CloudNotFound:
            cloud = {}
            _clouds_cache.put(cloud_id, cloud)
    if not cloud or cloud.get('deleted'):
        raise exception.CloudNotFound(id=cloud_id)
    return cloud

def _cloud_add(cloud):
    if 'id' not in cloud:
        cloud['id'] = _gen_uuid()
    cloud_id = cloud['id']
    back_cloud = flattening_dict(cloud)

    """ TODO: really add cloud. """
    result = db.cloud_create(default_context, back_cloud)
    global _clouds_cache
    _clouds_cache.put(cloud_id, result)
    return result

def _cloud_update(cloud_id, new_values):
    global _clouds_cache
    cloud = _cloud_get(cloud_id)
    # couldn't get here if not found
    flatten_new_values = flattening_dict(new_values)
    update_values = {}
    for k, v in flatten_new_values.items():
        if v != cloud.get(k, v) and k != 'id':
            update_values[k] = v

    new_cloud = cloud
    if update_values: ## update from db
        new_cloud = db.cloud_update(default_context, cloud_id, update_values)
        _clouds_cache.put(cloud_id, new_cloud)

    return new_cloud

def _cloud_delete(cloud_id):
    """ TODO: really delete cloud. """
    global _clouds_cache
    cloud = _clouds_cache.get(cloud_id)
    if (cloud is None) or not cloud.get('deleted'): # try to delete from db
        _clouds_cache.put(cloud_id, {'deleted', 1})
        db.cloud_delete(default_context, cloud_id)
    else:
        raise exception.CloudNotFound(id=cloud_id)

_gwclient_exc_dict = {}
def get_gatewayclient_exc(cloud):
    cloud_type = cloud['cloud_type'].lower()
    gwclient_exc = _gwclient_exc_dict.get(cloud_type)
    if not gwclient_exc:
        if cloud_type in ('openstack', 'fusionsphere'):
            client_kwargs = { 
                    'bypass_url': CONF.get('fs_gateway_url'), 
                    'insecure': True 
                    }
            gwclient = FSClient('1.0', **client_kwargs)
            exc = FSClient_Exc
            gwclient_exc = _gwclient_exc_dict[cloud_type] = gwclient, exc
        else:
            raise exception.CloudUnSupportedType(type=cloud_type)
    return gwclient_exc


def check_cloud_first(f):
    """ Check cloudid exists before do f."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        cloud_id = kwargs.pop('cloud_id')
        cloud = _cloud_get(cloud_id)
        kwargs['client'], client_exc = get_gatewayclient_exc(cloud)
        kwargs['client_exc'] = client_exc
        kwargs['region'] = cloud['availability_zone'] + '.' + cloud['region'] + '--' + cloud['cloud_type']

        try:
            return f(*args, **kwargs)
        except client_exc.ClientException as e: # just wrap the client exceptions
            raise exception.CMSException(message=e.message, code=e.code)
        except Exception as e:
            import pdb;pdb.set_trace()
            raise exception.UnexpectedError()

    return wrapper

class CloudController(wsgi.Application):
    _view_builder = clouds_view.ViewBuilder()
    
        
    def list(self, request):
        return self._view_builder.detail(request, db.cloud_get_all(default_context))

    def get_cloud(self, request, cloud_id):
        cloud = _cloud_get(cloud_id)
        return self._view_builder.show(request, cloud)

    def create_cloud(self, request, cloud):
        """ add cloud. """
        result = _cloud_add(cloud)
        return self._view_builder.show(request, result)

    def update_cloud(self, request, cloud_id, cloud):
        result = _cloud_update(cloud_id, cloud)
        return self._view_builder.show(request, result)

    def delete_cloud(self, request, cloud_id):
        _cloud_delete(cloud_id)
        return webob.Response(status_int=204)


class ResourceListController(wsgi.Application):
    _view_builder = None
    
    def list_hproject(self, request):
        """ TODO. """
        pass

    def list_hflavor(self, request):
        """ TODO. """
        pass

    def list_himage(self, request):
        """ TODO. """
        pass

    def list_project(self, request, cloud_id):
        """ TODO. """
        pass

    def list_flavor(self, request, cloud_id):
        """ TODO. """
        pass

    def list_image(self, request, cloud_id):
        """ TODO. """
        pass

def create_router(mapper):
    cloud_controller = CloudController()
    mapper.connect('/clouds',
                   controller=cloud_controller,
                   action='list',
                   conditions=dict(method=['GET']))
    mapper.connect('/clouds',
                   controller=cloud_controller,
                   action='create_cloud',
                   conditions=dict(method=['POST']))
    mapper.connect('/clouds/{cloud_id}',
                   controller=cloud_controller,
                   action='get_cloud',
                   conditions=dict(method=['GET']))
    mapper.connect('/clouds/{cloud_id}',
                   controller=cloud_controller,
                   action='update_cloud',
                   conditions=dict(method=['PUT']))
    mapper.connect('/clouds/{cloud_id}',
                   controller=cloud_controller,
                   action='delete_cloud',
                   conditions=dict(method=['DELETE']))
    resource_controller = ResourceListController()
    for name in ('project', 'flavor', 'image'):
        mapper.connect('/h%ss' % name, controller=resource_controller, 
                action='list_h%s'%name, conditions=dict(method=['GET']))
        mapper.connect('/{cloud_id}/%ss' % name, controller=resource_controller, 
                action='list_%s'%name, conditions=dict(method=['GET']))

