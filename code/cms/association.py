import webob
import wsgi
import db

from cms import exception

from cms.views import association as association_view

from cms.clouds import check_cloud_first

class AssociationController(wsgi.Application):

    def __init__(self, name):

        self.name = name  # project, flavor, image, network
        self._view_builder = association_view.ViewBuilder(name)
        
    @check_cloud_first
    def list(self, request, client, region, client_exc, **kwargs):
        client.associations.set_name(self.name)
        result = client.associations.findall(region=region)
        return self._view_builder.detail(request, result)

    @check_cloud_first
    def get(self, request, association_id, 
              client, region, client_exc, **kwargs):
        client.associations.set_name(self.name)
        found = True
        try:
            result = client.associations.get(association_id)
        except client_exc.NotFound:
            result = client.associations.find(region=region, id=association_id)

        if result.region != region:
            raise exception.AssociationNotFound(obj=self.name, id=association_id)

        return self._view_builder.show(request, result)

    @check_cloud_first
    def create(self, request, association, 
                client, region, client_exc, **kwargs):
        client.associations.set_name(self.name)
        association['region'] = region
        result = client.associations.create(**association)
        return self._view_builder.show(request, result)

    @check_cloud_first
    def update(self, request, association_id, association, 
                client, region, client_exc, **kwargs):
        client.associations.set_name(self.name)
        try:
            result = client.associations.get(association_id)
        except client_exc.NotFound:
            result = client.associations.find(region=region, id=association_id)

        if result.region != region:
            raise exception.AssociationNotFound(obj=self.name, id=association_id)

        result = client.associations.update(association_id, **association)
        return self._view_builder.show(request, result)

    @check_cloud_first
    def delete(self, request, association_id, 
                client, region, client_exc, **kwargs):
        client.associations.set_name(self.name)
        try:
            result = client.associations.get(association_id)
        except client_exc.NotFound:
            result = client.associations.find(region=region, id=association_id)

        if result.region != region:
            raise exception.AssociationNotFound(obj=self.name, id=association_id)

        result = client.associations.delete(association_id)
        return webob.Response(status_int=204)


def create_router(mapper):

    for name in ('project', 'image', 'flavor', 'network'):

        controller = AssociationController(name)
        path = '/{cloud_id}/%s_association' % name
        mapper.connect(path,
                       controller=controller,
                       action='list',
                       conditions=dict(method=['GET']))
        mapper.connect(path,
                       controller=controller,
                       action='create',
                       conditions=dict(method=['POST']))
        mapper.connect(path + '/{association_id}',
                       controller=controller,
                       action='get',
                       conditions=dict(method=['GET']))
        mapper.connect(path + '/{association_id}',
                       controller=controller,
                       action='update',
                       conditions=dict(method=['PUT']))
        mapper.connect(path + '/{association_id}',
                       controller=controller,
                       action='delete',
                       conditions=dict(method=['DELETE']))


def _filter_by_region(assocs, region, obj):
    res = {}
    if assocs:
        for a in assocs:
            if region == a.get('region'):
                res = a
                break
    if obj == 'project':
        return (res.get(obj),  res.get("userid"))
    return res.get(obj)

