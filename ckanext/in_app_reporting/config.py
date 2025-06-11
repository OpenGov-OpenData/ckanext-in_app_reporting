import logging
import ckan.plugins.toolkit as tk


log = logging.getLogger(__name__)


def metabase_site_url():
    metabase_site_url = tk.config.get(
        'ckanext.in_app_reporting.metabase_site_url')
    if not metabase_site_url:
        log.error('ckanext.in_app_reporting.metabase_site_url is not set')
    return metabase_site_url


def metabase_embedding_secret_key():
    metabase_embedding_secret_key = tk.config.get(
        'ckanext.in_app_reporting.metabase_embedding_secret_key')
    if not metabase_embedding_secret_key:
        log.error('ckanext.in_app_reporting.metabase_embedding_secret_key is not set')
    return metabase_embedding_secret_key


def metabase_jwt_shared_secret():
    metabase_jwt_shared_secret = tk.config.get(
        'ckanext.in_app_reporting.metabase_jwt_shared_secret')
    if not metabase_jwt_shared_secret:
        log.error('ckanext.in_app_reporting.metabase_jwt_shared_secret is not set')
    return metabase_jwt_shared_secret


def metabase_manage_service_url():
    metabase_manage_service_url = tk.config.get(
        'ckanext.in_app_reporting.metabase_manage_service_url')
    if not metabase_manage_service_url:
        log.error('ckanext.in_app_reporting.metabase_manage_service_url is not set')
    return metabase_manage_service_url


def metabase_manage_service_key():
    metabase_manage_service_key = tk.config.get(
        'ckanext.in_app_reporting.metabase_manage_service_key')
    if not metabase_manage_service_key:
        log.error('ckanext.in_app_reporting.metabase_manage_service_key is not set')
    return metabase_manage_service_key


def metabase_client_id():
    metabase_client_id = tk.config.get(
        'ckanext.in_app_reporting.metabase_client_id')
    if not metabase_client_id:
        log.error('ckanext.in_app_reporting.client_id is not set')
    return metabase_client_id


def metabase_api_key():
    metabase_api_key = tk.config.get(
        'ckanext.in_app_reporting.metabase_api_key')
    if not metabase_api_key:
        log.error('ckanext.in_app_reporting.metabase_api_key is not set')
    return metabase_api_key


def metabase_db_id():
    metabase_db_id = tk.config.get(
        'ckanext.in_app_reporting.metabase_db_id')
    if not metabase_db_id:
        log.error('ckanext.in_app_reporting.metabase_db_id is not set')
    return metabase_db_id


def collection_ids():
    collection_ids = tk.aslist(
        tk.config.get('ckanext.in_app_reporting.collection_ids', []))
    if not collection_ids:
        log.error('ckanext.in_app_reporting.collection_ids is not set')
    return collection_ids


def group_ids():
    group_ids = tk.aslist(
        tk.config.get('ckanext.in_app_reporting.group_ids', []))
    if not group_ids:
        log.error('ckanext.in_app_reporting.group_ids is not set')
    return group_ids
