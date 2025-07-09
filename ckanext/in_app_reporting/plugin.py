import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as df
import ckanext.in_app_reporting.action as action
import ckanext.in_app_reporting.auth as auth
import ckanext.in_app_reporting.cli as cli
import ckanext.in_app_reporting.utils as utils
import ckanext.in_app_reporting.blueprint as view

from six import text_type


boolean_validator = toolkit.get_validator(u'boolean_validator')
not_empty = toolkit.get_validator('not_empty')
missing = df.missing


class InAppReportingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)

    # IClick
    def get_commands(self):
        return cli.get_commands()

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'reporting')

    # IActions
    def get_actions(self):
        return {
            'metabase_mapping_create': action.metabase_mapping_create,
            'metabase_mapping_update': action.metabase_mapping_update,
            'metabase_mapping_delete': action.metabase_mapping_delete,
            'metabase_mapping_show': action.metabase_mapping_show,
            'metabase_mapping_list': action.metabase_mapping_list,
            'metabase_card_publish': action.metabase_card_publish,
            'metabase_dashboard_publish': action.metabase_dashboard_publish,
            'metabase_model_create': action.metabase_model_create
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'metabase_mapping_create': auth.metabase_mapping_create,
            'metabase_mapping_update': auth.metabase_mapping_update,
            'metabase_mapping_delete': auth.metabase_mapping_delete,
            'metabase_mapping_show': auth.metabase_mapping_show,
            'metabase_mapping_list': auth.metabase_mapping_list,
            'metabase_embed': auth.metabase_embed,
            'metabase_sso': auth.metabase_sso,
            'metabase_data': auth.metabase_data,
            'metabase_card_publish': auth.metabase_card_publish,
            'metabase_dashboard_publish': auth.metabase_dashboard_publish,
            'metabase_model_create': auth.metabase_model_create
        }

    # IBlueprint
    def get_blueprint(self):
        u'''Return a Flask Blueprint object to be registered by the app.'''
        return view.metabase

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'is_metabase_sso_user': utils.is_metabase_sso_user,
            'get_metabase_embeddable': utils.get_metabase_embeddable,
            'get_metabase_table_id': utils.get_metabase_table_id,
            'get_metabase_cards_by_table_id': utils.get_metabase_cards_by_table_id,
            'get_metabase_cards_by_resource_id': utils.get_metabase_cards_by_resource_id
        }


class MetabaseCardViewPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IResourceView, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)

    # IConfigurer
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

    # IResourceView
    def info(self):
        return {
            'name': 'metabase_card_view',
            'title': 'Embed Question',
            'default_title': 'Question',
            'icon': 'bar-chart',
            'always_available': False,
            'iframed': True,
            'preview_enabled': True,
            'schema': {
                'entity_id': [not_empty, text_type],
                'bordered': [configurable_defaults_validator(True), boolean_validator],
                'titled': [configurable_defaults_validator(True), boolean_validator]
            },
        }

    def can_view(self, data_dict):
        if not toolkit.g.userobj.sysadmin:
            return False
        resource = data_dict['resource']
        return resource.get('datastore_active', False)

    def view_template(self, context, data_dict):
        return 'metabase/card_view.html'

    def form_template(self, context, data_dict):
        return 'metabase/card_form.html'

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_metabase_iframe_url': utils.get_metabase_iframe_url
        }


class MetabaseDashboardViewPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IResourceView, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)

    # IConfigurer
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

    # IResourceView
    def info(self):
        return {
            'name': 'metabase_dashboard_view',
            'title': 'Embed Dashboard',
            'default_title': 'Dashboard',
            'icon': 'bar-chart',
            'always_available': False,
            'iframed': True,
            'preview_enabled': True,
            'schema': {
                'entity_id': [not_empty, text_type],
                'bordered': [configurable_defaults_validator(True), boolean_validator],
                'titled': [configurable_defaults_validator(True), boolean_validator],
                'downloads': [configurable_defaults_validator(True), boolean_validator]
            },
        }

    def can_view(self, data_dict):
        if not toolkit.g.userobj.sysadmin:
            return False
        resource = data_dict['resource']
        return resource.get('datastore_active', False)

    def view_template(self, context, data_dict):
        return 'metabase/dashboard_view.html'

    def form_template(self, context, data_dict):
        return 'metabase/dashboard_form.html'

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_metabase_iframe_url': utils.get_metabase_iframe_url
        }


def configurable_defaults_validator(default_configurable_value):
    def callable(key, data, errors, context):
        if context.get('for_view'):
            if data.get(key) is missing or data.get(key) is None or data.get(key) == '':
                data[key] = False
        else:
            data[key] = default_configurable_value
    return callable
