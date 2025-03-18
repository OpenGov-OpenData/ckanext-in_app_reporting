import requests
import ckan.plugins.toolkit as tk
import ckanext.in_app_reporting.config as mb_config
import ckanext.in_app_reporting.utils as utils


METABASE_SITE_URL = mb_config.metabase_site_url()
METABASE_API_KEY = mb_config.metabase_api_key()
METABASE_DB_ID = mb_config.metabase_db_id()
collection_ids = mb_config.collection_ids()


def metabase_publish_card(context, data_dict):
    tk.check_access('metabase_publish_card', context, data_dict)

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


def metabase_publish_dashboard(context, data_dict):
    tk.check_access('metabase_publish_dashboard', context, data_dict)

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


def metabase_create_model(context, data_dict):
    tk.check_access('metabase_create_model', context, data_dict)

    resource_id = data_dict.get('resource_id')
    if not resource_id:
        raise tk.ValidationError({'resource_id': 'Resource ID Required'})
    model_name = data_dict.get('model_name')
    if not model_name:
        raise tk.ValidationError({'model_name': 'Model Name Required'})

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
    data_dict = {
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
    response = utils.metabase_post_request(
        f'{METABASE_SITE_URL}/api/card', data_dict)
    if response:
        return {'success': True, 'result': response}
    else:
        raise tk.ValidationError({'error': 'Failed to publish card'})
