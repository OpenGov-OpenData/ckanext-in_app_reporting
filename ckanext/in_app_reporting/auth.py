import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.in_app_reporting.utils as utils


def metabase_mapping_create(context, data_dict):
    # Only sysadmins can access this
    return {'success': False}


def metabase_mapping_update(context, data_dict):
    # Only sysadmins can access this
    return {'success': False}


def metabase_mapping_delete(context, data_dict):
    # Only sysadmins can access this
    return {'success': False}


def metabase_mapping_show(context, data_dict):
    # Only sysadmins can access this
    return {'success': False}


def metabase_mapping_list(context, data_dict):
    # Only sysadmins can access this
    return {'success': False}


def metabase_embed(context, data_dict):
    # Only sysadmins can access this
    return {'success': False}


def metabase_sso(context, data_dict):
    # Only sysadmins can access this
    return {'success': False}


def metabase_data(context, data_dict):
    # Only sysadmins can access this
    return {'success': False}


def metabase_card_publish(context, data_dict):
    authorized = tk.check_access('resource_update', context, data_dict)
    user = context.get('user')
    userobj = model.User.get(user)
    if not authorized or not utils.is_metabase_sso_user(userobj):
        return {
            'success': False,
            'msg': tk._(
                'User {0} not authorized to publish card {1}'
                    .format(str(user), data_dict['id'])
            )
        }
    else:
        return {'success': True}


def metabase_dashboard_publish(context, data_dict):
    authorized = tk.check_access('resource_update', context, data_dict)
    user = context.get('user')
    userobj = model.User.get(user)
    if not authorized or not utils.is_metabase_sso_user(userobj):
        return {
            'success': False,
            'msg': tk._(
                'User {0} not authorized to publish dashboard {1}'
                    .format(str(user), data_dict['id'])
            )
        }
    else:
        return {'success': True}


def metabase_model_create(context, data_dict):
    # Only sysadmins can access this
    return {'success': False}
