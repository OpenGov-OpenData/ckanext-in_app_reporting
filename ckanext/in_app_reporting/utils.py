import datetime
import json
import jwt
import re
import requests
import time
import uuid
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.in_app_reporting.config as mb_config
from ckanext.in_app_reporting.model import MetabaseMapping


METABASE_SITE_URL = mb_config.metabase_site_url()
METABASE_EMBEDDING_SECRET_KEY = mb_config.metabase_embedding_secret_key()
METABASE_JWT_SHARED_SECRET = mb_config.metabase_jwt_shared_secret()
METABASE_API_KEY = mb_config.metabase_api_key()
METABASE_DB_ID = mb_config.metabase_db_id()
collection_ids = mb_config.collection_ids()
group_ids = mb_config.group_ids()

METABASE_MANAGE_SERVICE_URL = mb_config.metabase_manage_service_url()
METABASE_SERVICE_KEY = mb_config.metabase_manage_service_key()
METABASE_CLIENT_ID = mb_config.metabase_client_id()


def is_metabase_sso_user(userobj):
    if not userobj:
        return False
    user_name = userobj.name
    if re.match("[^@]+@[^@]+\.[^@]+", user_name, re.IGNORECASE):
        user = model.User.by_name(user_name)
        if user:
            if user.is_active() and not user.password:
                return True
    return False


def metabase_get_request(url):
    headers = {'x-api-key': METABASE_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None


def metabase_post_request(url, data_dict):
    headers = {
        'x-api-key': METABASE_API_KEY,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(data_dict)
        )
        return response.json()
    except Exception:
        return None


def metabase_manage_service_request(params, payload):
    headers = {
        'Authorization': 'Token {}'.format(METABASE_SERVICE_KEY),
        'Content-Type': 'application/json'
    }
    response = requests.post(
        f"{METABASE_MANAGE_SERVICE_URL}/api/v1/token",
        params=params,
        headers=headers,
        json=payload
    )
    try:
        token = response.json().get('token')
        if not token:
            raise tk.ValidationError({'error': 'Failed to retrieve Metabase token'})
        return token
    except json.JSONDecodeError:
        raise tk.ValidationError({'error': 'Failed to decode Metabase token response'})


def split_fullname(fullname):
    if fullname and len(fullname.split(' ')) >= 2:
        parts = fullname.split(' ')
        return parts[0], parts[-1]
    return None, None


def get_metabase_iframe_url(model_type, entity_id, bordered, titled, downloads):
    if METABASE_MANAGE_SERVICE_URL and METABASE_SERVICE_KEY:
        params = {
            'domain': METABASE_CLIENT_ID,
            'embedding_type': 'static',
        }
        payload = {
            "resources": {model_type: entity_id},
        }
        token = metabase_manage_service_request(params, payload)
    else:
        payload = {
            "resource": {model_type: entity_id},
            "params": {},
            "exp": round(time.time()) + (60 * 10) # 10 minute expiration
        }
        token = jwt.encode(payload, METABASE_EMBEDDING_SECRET_KEY, algorithm="HS256")
    iframeUrl = "{}/embed/{}/{}#bordered={}&titled={}&downloads={}".format(
        METABASE_SITE_URL,
        model_type,
        token,
        str(bordered).lower(),
        str(titled).lower(),
        str(downloads).lower(),
    )
    return iframeUrl


def get_metabase_user_token(userobj):
    metabase_mapping = tk.get_action('metabase_mapping_show')({}, {'user_id': userobj.id})
    if not metabase_mapping:
        # If no mapping exists, use default values
        metabase_mapping = {
            'platform_uuid': None,
            'group_ids': group_ids,
            'collection_ids': collection_ids
        }
    first_name, last_name = split_fullname(userobj.fullname)
    if METABASE_MANAGE_SERVICE_URL and METABASE_SERVICE_KEY:
        params = {
            'domain': METABASE_CLIENT_ID,
            'embedding_type': 'interactive',
            'og_user_id': metabase_mapping.get('platform_uuid'),
        }
        payload = {
            'email': userobj.name,
            'groups': metabase_mapping.get('group_ids')
        }
        if first_name and last_name:
            payload['firstName'] = first_name
            payload['lastName'] = last_name
        token = metabase_manage_service_request(params, payload)
    else:
        payload = {
            "email": userobj.name,
            "exp": round(time.time()) + (60 * 10),  # 10 minute expiration
            "groups": metabase_mapping.get("group_ids")
        }
        if first_name and last_name:
            payload["first_name"] = first_name
            payload["last_name"] = last_name
        token = jwt.encode(payload, METABASE_JWT_SHARED_SECRET, algorithm="HS256")
    return token


def get_metabase_embeddable(model_type):
    embeddable_items = []
    if model_type not in ['dashboard', 'card']:
        return embeddable_items
    # Get all embeddable of specific model type
    all_embeddables = metabase_get_request(
        f'{METABASE_SITE_URL}/api/{model_type}/embeddable')
    if not all_embeddables:
        return embeddable_items
    embeddable_items = [item.get('id') for item in all_embeddables]
    return embeddable_items


def get_metabase_collection_id():
    if len(collection_ids) > 0:
        collection_id = collection_ids[0]
        return collection_id
    else:
        return ''


def get_metabase_table_id(table_name):
    table_id = None
    result = metabase_get_request(
        f'{METABASE_SITE_URL}/api/database/{METABASE_DB_ID}?include=tables')
    if not result:
        return table_id
    for table in result.get('tables', []):
        if table.get('name') == table_name:
            table_id = table.get('id')
            break
    return table_id


def get_metabase_model_id(table_id):
    card_results = metabase_get_request(f'{METABASE_SITE_URL}/api/card?f=table&model_id={table_id}')
    model_id = ''
    if not card_results:
        return model_id
    for card in card_results:
        if card.get('type') == 'model':
            model_id = card.get('id')
            break
    return model_id


def get_metabase_cards_by_table_id(table_id):
    userobj = tk.g.userobj
    metabase_mapping = tk.get_action('metabase_mapping_show')({}, {'user_id': userobj.id})
    matching_cards = []
    card_results = metabase_get_request(f'{METABASE_SITE_URL}/api/card?f=table&model_id={table_id}')
    if not card_results:
        return matching_cards
    for card in card_results:
        if str(card.get('collection_id')) in metabase_mapping['collection_ids']:
            matching_cards.append({
                'id': card.get('id'),
                'name': card.get('name'),
                'type': card.get('type'),
                'updated_at': card.get('updated_at')
            })
    matching_cards.sort(key=lambda card: (card['type'], card['name']))
    return matching_cards


def get_metabase_sql_questions(resource_id):
    userobj = tk.g.userobj
    metabase_mapping = tk.get_action('metabase_mapping_show')({}, {'user_id': userobj.id})
    matching_cards = []
    card_results = metabase_get_request(f'{METABASE_SITE_URL}/api/card?f=database&model_id={METABASE_DB_ID}')
    if not card_results:
        return matching_cards
    for card in card_results:
        if str(card.get('collection_id')) in metabase_mapping['collection_ids'] and not card.get('table_id'):
            if resource_id in card.get('dataset_query', {}).get('native',{}).get('query', ''):
                matching_cards.append({
                    'id': card.get('id'),
                    'name': card.get('name'),
                    'type': card.get('type'),
                    'updated_at': card.get('updated_at')
                })
    matching_cards.sort(key=lambda card: (card['type'], card['name']))
    return matching_cards


def get_metabase_collection_items(model_type):
    userobj = tk.g.userobj
    metabase_mapping = tk.get_action('metabase_mapping_show')({}, {'user_id': userobj.id})
    collection_items = []
    if model_type not in ['dashboard', 'card']:
        return collection_items
    # Get items of specific model type from specific collections
    for collection_id in metabase_mapping['collection_ids']:
        collection_results = metabase_get_request(
            f'{METABASE_SITE_URL}/api/collection/{collection_id}/items?models={model_type}')
        if not collection_results:
            continue
        for item in collection_results.get('data', []):
            item['text'] = item.get('name', '')
            collection_items.append(item)
    return collection_items


def metabase_mapping_create(data_dict):
    user_id = data_dict.get('user_id')
    if not user_id:
        raise tk.ValidationError({'user_id': 'User ID is required'})

    user = model.User.get(user_id)
    if not user:
        raise tk.ValidationError({'User ID': f'User with ID {user_id} not found'})

    # Check if already exists
    existing = MetabaseMapping.get(user_id=user_id)
    if existing:
        raise tk.ValidationError({'user_id': 'Mapping already exists. Use update instead.'})

    if data_dict.get('platform_uuid'):
        try:
            uuid.UUID(data_dict.get('platform_uuid'))
            platform_uuid = data_dict.get('platform_uuid')
        except ValueError:
            raise tk.ValidationError({'platform_uuid': 'OpenGov User UUID must be a valid UUID string'})
    else:
        try:
            from ckanext.opengov.auth.db import UserToken
            user_token = model.Session.query(UserToken).filter_by(user_name=user.email).first()
            if user_token:
                platform_uuid = user_token.platform_uuid
        except Exception as e:
            raise tk.ValidationError({'platform_uuid': 'OpenGov User UUID not found'})

    group_ids = data_dict.get('group_ids', [])
    if not isinstance(group_ids, list):
        raise tk.ValidationError({'group_ids': 'Group IDs must be a list'})
    if not all(isinstance(item, str) for item in group_ids):
        raise tk.ValidationError({'group_ids': 'All group IDs must be strings'})

    collection_ids = data_dict.get('collection_ids', [])
    if not isinstance(collection_ids, list):
        raise tk.ValidationError({'collection_ids': 'Collection IDs must be a list'})
    if not all(isinstance(item, str) for item in collection_ids):
        raise tk.ValidationError({'collection_ids': 'All collection IDs must be strings'})

    group_ids_str = ';'.join(group_ids)
    collection_ids_str = ';'.join(collection_ids)

    mapping = MetabaseMapping(
        user_id=user_id,
        platform_uuid=platform_uuid,
        email=user.email,
        group_ids=group_ids_str,
        collection_ids=collection_ids_str,
        created=datetime.datetime.utcnow(),
        modified=datetime.datetime.utcnow()
    )

    model.Session.add(mapping)
    model.Session.commit()

    return {
        "user_id": user_id,
        "platform_uuid": mapping.platform_uuid,
        "email": mapping.email,
        "group_ids": group_ids,
        "collection_ids": collection_ids,
        "created": mapping.created.isoformat(),
        "modified": mapping.modified.isoformat()
    }


def metabase_mapping_update(data_dict):
    user_id = data_dict.get('user_id')
    if not user_id:
        raise tk.ValidationError({'user_id': 'User ID is required'})

    user = model.User.get(user_id)
    if not user:
        raise tk.ValidationError({'User ID': f'User with ID {user_id} does not exist'})

    mapping = MetabaseMapping.get(user_id=user_id)
    if not mapping:
        raise tk.ObjectNotFound(f'No mapping found for user_id={user_id}')

    if data_dict.get('platform_uuid'):
        try:
            uuid.UUID(data_dict.get('platform_uuid'))
            mapping.platform_uuid = data_dict.get('platform_uuid')
        except ValueError:
            raise tk.ValidationError({'platform_uuid': 'OpenGov User UUID must be a valid UUID string'})

    group_ids = data_dict.get('group_ids', mapping.group_ids or [])
    if not isinstance(group_ids, list):
        raise tk.ValidationError({'group_ids': 'Group IDs must be a list'})
    if not all(isinstance(item, str) for item in group_ids):
        raise tk.ValidationError({'group_ids': 'All group IDs must be strings'})

    collection_ids = data_dict.get('collection_ids', mapping.collection_ids or [])
    if not isinstance(collection_ids, list):
        raise tk.ValidationError({'collection_ids': 'Collection IDs must be a list'})
    if not all(isinstance(item, str) for item in collection_ids):
        raise tk.ValidationError({'collection_ids': 'All collection IDs must be strings'})

    mapping.email = user.email
    mapping.group_ids = ';'.join(group_ids)
    mapping.collection_ids = ';'.join(collection_ids)
    mapping.modified = datetime.datetime.utcnow()

    model.Session.commit()

    return {
        "user_id": user_id,
        "platform_uuid": mapping.platform_uuid,
        "email": mapping.email,
        "group_ids": [g.strip() for g in mapping.group_ids.split(';')],
        "collection_ids": [c.strip() for c in mapping.collection_ids.split(';')],
        "created": mapping.created.isoformat(),
        "modified": mapping.modified.isoformat()
    }


def metabase_mapping_delete(data_dict):
    user_id = data_dict.get('user_id')
    if not user_id:
        raise tk.ValidationError({'user_id': 'User ID is required'})

    mapping = MetabaseMapping.get(user_id=user_id)
    if not mapping:
        raise tk.ObjectNotFound(f'No mapping found for user_id {user_id}')

    model.Session.delete(mapping)
    model.Session.commit()

    return {'message': f'Mapping for user_id {user_id} deleted successfully.'}
