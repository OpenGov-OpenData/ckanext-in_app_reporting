from flask import Blueprint, request
from flask.views import MethodView
from urllib.parse import urlencode, urljoin

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.in_app_reporting.utils as utils
import ckanext.in_app_reporting.config as mb_config


METABASE_SITE_URL = mb_config.metabase_site_url()
metabase = Blueprint(u'metabase', __name__)


class MetabaseView(MethodView):
    def metabase_embed():
        if not utils.is_metabase_sso_user(tk.g.userobj):
            tk.abort(404, tk._(u'Resource not found'))
        try:
            context = {
                u'model': model,
                u'user': tk.g.user,
                u'auth_user_obj': tk.g.userobj
            }
            tk.check_access('metabase_embed', context, {})
            return_to = request.args.get("return_to", "/")
        except tk.NotAuthorized:
            tk.abort(404, tk._(u'Resource not found'))
        return tk.render(
            u'metabase/metabase.html',
            extra_vars={
                'return_to': return_to,
                'site_url': tk.config.get('ckan.site_url')
            }
        )

    def metabase_sso():
        if not utils.is_metabase_sso_user(tk.g.userobj):
            tk.abort(404, tk._(u'Resource not found'))
        try:
            context = {
                u'model': model,
                u'user': tk.g.user,
                u'auth_user_obj': tk.g.userobj
            }
            tk.check_access('metabase_sso', context, {})
            jwt_token = utils.get_metabase_user_token(tk.g.userobj)
            sso_url = urljoin(METABASE_SITE_URL, "/auth/sso")
            return_to = request.args.get("return_to", "/")
            return_to_with_ui_flags = f"{return_to}?top_nav=true&search=true&new_button=true&entity_type=model"
            query_params = urlencode({
                "jwt": jwt_token,
                "return_to": return_to_with_ui_flags
            })
            redirect_url = f"{sso_url}?{query_params}"
            return tk.redirect_to(redirect_url)
        except tk.NotAuthorized:
            tk.abort(404, tk._(u'Resource not found'))

    def metabase_data(id, resource_id):
        if not utils.is_metabase_sso_user(tk.g.userobj):
            tk.abort(404, tk._(u'Resource not found'))
        try:
            context = {
                u'model': model,
                u'user': tk.g.user,
                u'auth_user_obj': tk.g.userobj
            }
            tk.check_access('metabase_data', context, {})
        except tk.NotAuthorized:
            tk.abort(404, tk._(u'Resource not found'))
        try:
            pkg_dict = tk.get_action('package_show')(None, {'id': id})
            resource = tk.get_action('resource_show')(None, {'id': resource_id})
        except (tk.ObjectNotFound, tk.NotAuthorized):
            return tk.abort(404, tk._('Resource not found'))

        if request.method == 'POST':
            redirect_url = tk.url_for('metabase.metabase_data', id=id, resource_id=resource_id)
            try:
                resource_name = resource.get('name') or resource.get('id')
                model_name = '%s - %s' % (pkg_dict.get('title'), resource_name)
                model_dict = {
                    'resource_id': resource_id,
                    'name': model_name
                }
                if resource.get('description'):
                    model_dict['description'] = resource.get('description')
                model_result = tk.get_action('metabase_model_create')({'ignore_auth': True}, model_dict)
                if not model_result.get('success'):
                    tk.h.flash_error(tk._('Failed to create model'))
                return tk.redirect_to(redirect_url)
            except Exception as err:
                tk.h.flash_error('Failed to create model')

        extra_vars = {
            'pkg_dict': pkg_dict,
            'resource': resource
        }
        return tk.render(
            u'metabase/metabase_data.html',
            extra_vars=extra_vars
        )

    def get_metabase_collection_items(model_type):
        if not utils.is_metabase_sso_user(tk.g.userobj):
            tk.abort(404, tk._(u'Resource not found'))
        try:
            context = {
                u'model': model,
                u'user': tk.g.user,
                u'auth_user_obj': tk.g.userobj
            }
            tk.check_access('metabase_embed', context, {})
            if model_type == 'question':
                model_type = 'card'
            embeddable_list = utils.get_metabase_collection_items(model_type)
            data = {
                'results': embeddable_list
            }
            return data
        except tk.NotAuthorized:
            tk.abort(404, tk._(u'Resource not found'))


metabase.add_url_rule(
    u'/insights',
    view_func=MetabaseView.metabase_embed,
    methods=[u'GET']
)

metabase.add_url_rule(
    u'/sso/metabase/',
    view_func=MetabaseView.metabase_sso,
    methods=[u'GET']
)

metabase.add_url_rule(
    u'/dataset/<id>/insights/<resource_id>',
    view_func=MetabaseView.metabase_data,
    methods=[u'GET', u'POST']
)

metabase.add_url_rule(
    u'/get_metabase_collection_items/<string:model_type>',
    view_func=MetabaseView.get_metabase_collection_items,
    methods=[u'GET']
)
