import requests
import ckan.plugins.toolkit as tk
import ckanext.in_app_reporting.config as mb_config
import ckanext.in_app_reporting.utils as utils


METABASE_SITE_URL = mb_config.metabase_site_url()
METABASE_API_KEY = mb_config.metabase_api_key()


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
