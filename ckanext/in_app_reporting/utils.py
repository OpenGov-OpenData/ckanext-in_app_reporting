import json
import jwt
import re
import requests
import time
import ckan.model as model
import ckanext.in_app_reporting.config as mb_config


METABASE_SITE_URL = mb_config.metabase_site_url()
METABASE_EMBEDDING_SECRET_KEY = mb_config.metabase_embedding_secret_key()
METABASE_JWT_SHARED_SECRET = mb_config.metabase_jwt_shared_secret()
METABASE_API_KEY = mb_config.metabase_api_key()
METABASE_DB_ID = mb_config.metabase_db_id()
collection_ids = mb_config.collection_ids()
group_ids = mb_config.group_ids()


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


def get_metabase_iframe_url(model_type, entity_id, bordered, titled, downloads):
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
    payload = {
        "email": userobj.name,
        "exp": round(time.time()) + (60 * 10) # 10 minute expiration
    }
    payload["groups"] = group_ids
    fullname = userobj.fullname
    if fullname and len(fullname.split(' ')) >= 2:
        first_name = fullname.split(' ')[0]
        last_name = fullname.split(' ')[-1]
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


def get_metabase_cards_by_table_id(table_id):
    matching_cards = []
    card_results = metabase_get_request(f'{METABASE_SITE_URL}/api/card?f=table&model_id={table_id}')
    for card in card_results:
        if str(card.get('collection_id')) in collection_ids:
            matching_cards.append({
                'id': card.get('id'),
                'name': card.get('name'),
                'type': card.get('type'),
                'updated_at': card.get('updated_at')
            })
    matching_cards.sort(key=lambda card: (card['type'], card['name']))
    return matching_cards


def get_metabase_collection_items(model_type):
    collection_items = []
    if model_type not in ['dashboard', 'card']:
        return collection_items
    # Get items of specific model type from specific collections
    for collection_id in collection_ids:
        collection_results = metabase_get_request(
            f'{METABASE_SITE_URL}/api/collection/{collection_id}/items?models={model_type}')
        if not collection_results:
            continue
        for item in collection_results.get('data', []):
            item['text'] = item.get('name', '')
            collection_items.append(item)
    return collection_items
