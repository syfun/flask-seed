# coding=utf-8

from flask import blueprints, make_response, request, \
    jsonify, current_app as app

from flask_seed.exceptions import HTTPNotFound, HTTPBadRequest, \
    HTTPInternalServerError
from flask_seed.utils import parse_params, remove_dict_item, dumps, LOG


class BaseHandler(object):
    """
    BaseHandler to handle request.

    permissions are handle func's permission. Example:
        {
            "on_all": "viewAll"
        }
    """
    model = ''
    member = ''
    create_required_fields = []
    other_fields = []
    permissions = {}

    def __init__(self, blueprint_name=None):
        if not blueprint_name:
            blueprint_name = self.member
        self.blueprint = blueprints.Blueprint(blueprint_name, __name__)

        self._model = getattr(app.db_driver, self.model)

        self.generate_url()
        self.handle_url_route()

        self.all_fields = self.create_required_fields + self.other_fields

    def generate_url(self):
        prefix = ''
        self.set_url = '{prefix}/{member}s'.format(
            prefix=prefix, member=self.member)
        self.member_url = '{set_url}/<{member}_id>'.format(
            set_url=self.set_url, member=self.member)

    def _get_resource_id(self, member, **kwargs):
        key = '{}_id'.format(member)
        return int(kwargs.get(key))

    def get_filter(self):
        params = parse_params()
        limit = int(remove_dict_item(params, 'limit', 0))
        page = int(remove_dict_item(params, 'page', 1))
        per_page = int(remove_dict_item(params, 'per_page', 0))
        if per_page:
            limit = per_page
        skip = (page - 1) * per_page

        projection = remove_dict_item(params, 'columns')
        if projection:
            projection = projection.split(',')
        filter = params
        return filter, limit, skip, projection

    def get_post_data(self, operation=None, resource_id=None):
        data = request.get_json()
        if operation == 'create':
            for key in self.create_required_fields:
                if key not in data:
                    err_msg = '{} field must be not None.'.format(key)
                    raise HTTPBadRequest(err_msg)
        elif operation == 'update':
            if self.all_fields:
                for key in data.keys():
                    if key not in self.all_fields:
                        err_msg = 'Cannot accept {} filed.'.format(key)
                        raise HTTPBadRequest(err_msg)
        return data

    def get_post_projection(self):
        return None

    def get_projection(self):
        projection = request.args.get('columns', None)
        if projection:
            projection = projection.split(',')
        return projection

    def query(self, **kwargs):
        filter, limit, skip, projection = self.get_filter()
        resources = self._model.query(
            filter=filter,
            limit=limit, skip=skip,
            projection=projection
        )
        return resources

    def on_all(self, **kwargs):
        resources = self.query(**kwargs)
        total = resources.count()
        if request.method == 'HEAD':
            response = make_response()
        else:
            response = make_response(dumps(resources))
        response.headers['Total'] = total
        return response

    def on_get(self, **kwargs):
        resource_id = self._get_resource_id(self.member, **kwargs)
        projection = self.get_projection()
        resource = self._model.get(resource_id, projection=projection)
        if not resource:
            err_msg = '{member} {_id} not found.'.format(
                member=self.member.capitalize(),
                _id=resource_id
            )
            raise HTTPNotFound(err_msg)
        return jsonify(resource)

    def on_create(self, **kwargs):
        resource = self.get_post_data('create')
        projection = self.get_post_projection()
        try:
            new_resource = self._model.create(resource)
        except Exception as e:
            app.logger.error(e)
            msg = 'Cannot create {0}, {1}.'.format(self.member, str(e))
            raise HTTPInternalServerError(msg)
        else:
            if isinstance(projection, list):
                for key in projection:
                    del new_resource[key]
            if isinstance(projection, dict):
                for key, value in projection.iteritems():
                    if not value:
                        del new_resource[key]
            return jsonify(new_resource), 201

    def on_update(self, **kwargs):
        resource_id = self._get_resource_id(self.member, **kwargs)
        resource = self.get_post_data('update', resource_id)
        projection = self.get_post_projection()
        if u'_id' in resource:
            del resource[u'_id']
        try:
            new_resource = self._model.update(resource_id, resource,
                                              projection=projection)
        except Exception as e:
            app.logger.error(str(e))
            msg = 'Cannot update {0}, {1}.'.format(self.member, str(e))
            raise HTTPInternalServerError(msg)
        else:
            err_msg = '{member} {_id} not found.'.format(
                member=self.member.capitalize(),
                _id=resource_id
            )
            if not new_resource:
                raise HTTPNotFound(err_msg)
            return jsonify(new_resource)

    def remove_check(self, resource_id):
        pass

    def on_delete(self, **kwargs):
        resource_id = self._get_resource_id(self.member, **kwargs)
        self.remove_check(resource_id)
        try:
            self._model.delete(resource_id)
        except Exception as e:
            app.logger.error(e)
            msg = 'Delete {0} failed, {1}'.format(self.member, str(e))
            raise HTTPInternalServerError(msg)
        else:
            return '', 204

    def route(self, url, view_func, methods=None):
        if methods is None:
            methods = ['GET']
        self.blueprint.add_url_rule(url, view_func=view_func, methods=methods)

    def handle_url_route(self):
        self.route(self.set_url, self.on_all, methods=['GET', 'HEAD'])
        self.route(self.member_url, self.on_get)
        log_create = LOG('Create {}'.format(self.member))
        log_update = LOG('Update {}'.format(self.member))
        log_delete = LOG('Delete {}'.format(self.member))
        self.route(self.set_url, log_create(self.on_create), ['POST'])
        self.route(self.member_url, log_update(self.on_update), ['POST'])
        self.route(self.member_url, log_delete(self.on_delete), ['DELETE'])
