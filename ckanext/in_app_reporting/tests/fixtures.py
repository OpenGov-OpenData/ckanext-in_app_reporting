import pytest
import ckan.tests.factories as factories
from unittest import mock
import ckan.model as model
from ckanext.in_app_reporting.model import MetabaseMapping


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("in_app_reporting")


@pytest.fixture
def metabase_mapping_factory():
    """Factory for creating MetabaseMapping objects"""
    def create_mapping(**kwargs):
        user = factories.User() if 'user_id' not in kwargs else None
        defaults = {
            'user_id': user['id'] if user else 'test-user-id',
            'platform_uuid': '12345678-1234-1234-1234-123456789012',
            'email': 'test@example.com',
            'group_ids': 'group1;group2',
            'collection_ids': '1;2'
        }
        defaults.update(kwargs)

        mapping = MetabaseMapping(**defaults)
        model.Session.add(mapping)
        model.Session.commit()
        return mapping
    return create_mapping


@pytest.fixture
def mock_metabase_config():
    """Mock metabase configuration values"""
    with mock.patch('ckanext.in_app_reporting.config.metabase_site_url', return_value='https://example.com'), \
         mock.patch('ckanext.in_app_reporting.config.metabase_api_key', return_value='test-key'), \
         mock.patch('ckanext.in_app_reporting.config.metabase_db_id', return_value='4'), \
         mock.patch('ckanext.in_app_reporting.config.collection_ids', return_value=['group1', 'group2']), \
         mock.patch('ckanext.in_app_reporting.config.group_ids', return_value=['1', '2']):
        yield


@pytest.fixture
def mock_requests():
    """Mock requests module for Metabase API calls"""
    with mock.patch('requests.get') as mock_get, \
         mock.patch('requests.post') as mock_post, \
         mock.patch('requests.put') as mock_put:

        # Default successful responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'data': []}

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'id': 123, 'success': True}

        mock_put.return_value.status_code = 200
        mock_put.return_value.json.return_value = {'success': True}

        yield {
            'get': mock_get,
            'post': mock_post,
            'put': mock_put
        }


@pytest.fixture
def mock_is_metabase_sso_user():
    """Mock the is_metabase_sso_user function"""
    with mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user', return_value=True) as mock_func:
        yield mock_func


@pytest.fixture
def mock_check_access():
    """Mock the check_access function"""
    with mock.patch('ckan.plugins.toolkit.check_access', return_value=None) as mock_func:
        yield mock_func
