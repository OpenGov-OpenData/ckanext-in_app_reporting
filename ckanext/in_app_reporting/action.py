import datetime
import requests
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.in_app_reporting.config as mb_config
import ckanext.in_app_reporting.utils as utils
from ckanext.in_app_reporting.model import MetabaseMapping


METABASE_SITE_URL = mb_config.metabase_site_url()
METABASE_API_KEY = mb_config.metabase_api_key()
METABASE_DB_ID = mb_config.metabase_db_id()
collection_ids = mb_config.collection_ids()


def metabase_mapping_create(context, data_dict):
    tk.check_access('metabase_mapping_create', context, data_dict)
    try:
        create_response = utils.metabase_mapping_create(data_dict)
        return create_response
    except Exception as e:
        raise tk.ValidationError({'error': str(e)})


def metabase_mapping_update(context, data_dict):
    tk.check_access('metabase_mapping_update', context, data_dict)
    try:
        update_response = utils.metabase_mapping_update(data_dict)
        return update_response
    except Exception as e:
        raise tk.ValidationError({'error': str(e)})


def metabase_mapping_delete(context, data_dict):
    tk.check_access('metabase_mapping_delete', context, data_dict)
    try:
        delete_response = utils.metabase_mapping_delete(data_dict)
        return delete_response
    except Exception as e:
        raise tk.ValidationError({'error': str(e)})


@tk.side_effect_free
def metabase_mapping_show(context, data_dict):
    tk.check_access('metabase_mapping_show', context, data_dict)

    user_id = data_dict.get('user_id')
    email = data_dict.get('email')
    if not user_id and not email:
        raise tk.ValidationError({'id': 'Provide either user id or email'})

    query = model.Session.query(MetabaseMapping).autoflush(False)
    if user_id:
        mapping = query.filter_by(user_id=user_id).first()
    else:
        mapping = query.filter_by(email=email).first()

    if not mapping:
        return {
            "user_id": user_id,
            "platform_uuid": "",
            "email": email,
            "group_ids": [],
            "collection_ids": []
        }

    return {
        "user_id": mapping.user_id,
        "platform_uuid": mapping.platform_uuid,
        "email": mapping.email,
        "group_ids": [g.strip() for g in mapping.group_ids.split(';')],
        "collection_ids": [c.strip() for c in mapping.collection_ids.split(';')]
    }


@tk.side_effect_free
def metabase_mapping_list(context, data_dict):
    tk.check_access('metabase_mapping_list', context, data_dict)

    query = model.Session.query(MetabaseMapping).autoflush(False)
    mappings = query.all()

    mapping_list = []
    for mapping in mappings:
        mapping_list.append({
            "user_id": mapping.user_id,
            "platform_uuid": mapping.platform_uuid,
            "email": mapping.email,
            "group_ids": [g.strip() for g in mapping.group_ids.split(';')],
            "collection_ids": [c.strip() for c in mapping.collection_ids.split(';')]
        })
    return mapping_list

@tk.side_effect_free
def metabase_sql_questions_list(context, data_dict):
    tk.check_access('metabase_model_create', context, data_dict)

    resource_id = data_dict.get('resource_id')
    if not resource_id or not isinstance(resource_id, str):
        raise tk.ValidationError({'resource_id': 'Resource ID required'})

    # try:
    #     tk.get_action('resource_show')(None, {'id': resource_id})
    # except (tk.ObjectNotFound, tk.NotAuthorized):
    #     raise tk.ValidationError({'error': 'Resource not found'})

    questions = utils.get_metabase_sql_questions(resource_id)
    if not questions:
        return []
    return questions

def metabase_card_publish(context, data_dict):
    tk.check_access('metabase_card_publish', context, data_dict)

    card_id = data_dict.get('id')
    if not card_id:
        raise tk.ValidationError({'id': 'Card ID Required'})

    headers = {
        'x-api-key': METABASE_API_KEY,
        'Content-Type': 'application/json'
    }
    metabase_url = f"{METABASE_SITE_URL}/api/card/{card_id}"
    payload = {
        'enable_embedding': True
    }

    # Call Metabase API to publish
    response = requests.put(metabase_url, json=payload, headers=headers)
    if response.status_code == 200:
        return {'success': True}
    else:
        raise tk.ValidationError({'error': 'Failed to publish card'})


def metabase_dashboard_publish(context, data_dict):
    tk.check_access('metabase_dashboard_publish', context, data_dict)

    dashboard_id = data_dict.get('id')
    if not dashboard_id:
        raise tk.ValidationError({'id': 'Dashboard ID Required'})

    headers = {
        'x-api-key': METABASE_API_KEY,
        'Content-Type': 'application/json'
    }
    metabase_url = f"{METABASE_SITE_URL}/api/dashboard/{dashboard_id}"
    payload = {
        'enable_embedding': True,
        'embedding_params': {}
    }

    # If configured, enable parameters
    if data_dict.get('enable_params'):
        dashboard = requests.get(metabase_url, headers=headers)
        dashboard = dashboard.json()
        embedding_params = {}
        for parameter in dashboard.get('parameters', []):
            embedding_params[parameter.get('slug')] = 'enabled'
        payload['embedding_params'] = embedding_params

    # Call Metabase API to publish
    response = requests.put(metabase_url, json=payload, headers=headers)
    if response.status_code == 200:
        return {'success': True}
    else:
        raise tk.ValidationError({'error': 'Failed to publish dashboard'})


def metabase_model_create(context, data_dict):
    tk.check_access('metabase_model_create', context, data_dict)

    resource_id = data_dict.get('resource_id')
    if not resource_id or not isinstance(resource_id, str):
        raise tk.ValidationError({'resource_id': 'Resource ID required'})
    model_name = data_dict.get('name')
    if not model_name or not isinstance(resource_id, str):
        raise tk.ValidationError({'name': 'Model name required'})

    try:
        resource = tk.get_action('resource_show')(None, {'id': resource_id})
    except (tk.ObjectNotFound, tk.NotAuthorized):
        raise tk.ValidationError({'error': 'Resource not found'})

    search_results = utils.metabase_get_request(
        f'{METABASE_SITE_URL}/api/search/?q={resource_id}&table_db_id={METABASE_DB_ID}&model=table')
    if not search_results:
        raise tk.ValidationError({'error': 'Failed to find resource in Metabase'})

    for item in search_results.get('data', []):
        if item.get('table_name') == resource_id:
            table_id = item.get('table_id')
            break
    if not table_id:
        raise tk.ValidationError({'error': 'Failed to find matching table for resource in Metabase'})

    query_metadata = utils.metabase_get_request(
        f'{METABASE_SITE_URL}/api/table/{table_id}/query_metadata')
    fields = []
    for item in query_metadata.get('fields', []):
        if item.get('name') != '_full_text':
            fields.append(
                [
                    'field',
                    item.get('id'),
                    {
                        'base_type': item.get('base_type'),
                    }
                ]
            )
    model_dict = {
        "name": model_name,
        "dataset_query": {
            "database": int(METABASE_DB_ID),
            "type": "query",
            "query": {
                "source-table": int(table_id),
                "fields": fields
            }
        },
        "display": "table",
        "displayIsLocked": True,
        "visualization_settings": {},
        "collection_id": int(collection_ids[0]),
        "type": "model"
    }
    if data_dict.get('description') and isinstance(data_dict.get('description'), str):
        model_dict['description'] = data_dict.get('description')
    response = utils.metabase_post_request(
        f'{METABASE_SITE_URL}/api/card', model_dict)
    if response:
        return {'success': True, 'result': response}
    else:
        raise tk.ValidationError({'error': 'Failed to publish card'})
