"""
Tests for utils.py utility functions.
"""
import pytest
import json
from unittest import mock
import ckan.model as model
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories

import ckanext.in_app_reporting.utils as utils


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestUserValidation:
    """Test user validation utility functions"""

    def test_is_metabase_sso_user_with_valid_sso_user(self):
        """Test is_metabase_sso_user with valid SSO user"""
        user = mock.Mock()
        user.name = 'test@example.com'
        user.is_active.return_value = True
        user.password = None

        with mock.patch('ckanext.in_app_reporting.utils.user_is_admin_or_editor', return_value=True), \
             mock.patch('ckan.model.User.by_name', return_value=user):
            result = utils.is_metabase_sso_user(user)

        assert result is True

    def test_is_metabase_sso_user_with_no_user(self):
        """Test is_metabase_sso_user with no user object"""
        result = utils.is_metabase_sso_user(None)
        assert result is False

    def test_is_metabase_sso_user_with_non_admin_user(self):
        """Test is_metabase_sso_user with non-admin user"""
        user = mock.Mock()
        user.name = 'test@example.com'

        with mock.patch('ckanext.in_app_reporting.utils.user_is_admin_or_editor', return_value=False):
            result = utils.is_metabase_sso_user(user)

        assert result is False

    def test_is_metabase_sso_user_with_invalid_email_format(self):
        """Test is_metabase_sso_user with invalid email format"""
        user = mock.Mock()
        user.name = 'invalid-email'

        with mock.patch('ckanext.in_app_reporting.utils.user_is_admin_or_editor', return_value=True):
            result = utils.is_metabase_sso_user(user)

        assert result is False

    def test_is_metabase_sso_user_with_inactive_user(self):
        """Test is_metabase_sso_user with inactive user"""
        user = mock.Mock()
        user.name = 'test@example.com'
        user.is_active.return_value = False
        user.password = None

        with mock.patch('ckanext.in_app_reporting.utils.user_is_admin_or_editor', return_value=True), \
             mock.patch('ckan.model.User.by_name', return_value=user):
            result = utils.is_metabase_sso_user(user)

        assert result is False

    def test_is_metabase_sso_user_with_password_user(self):
        """Test is_metabase_sso_user with user that has password"""
        user = mock.Mock()
        user.name = 'test@example.com'
        user.is_active.return_value = True
        user.password = 'hashed_password'

        with mock.patch('ckanext.in_app_reporting.utils.user_is_admin_or_editor', return_value=True), \
             mock.patch('ckan.model.User.by_name', return_value=user):
            result = utils.is_metabase_sso_user(user)

        assert result is False

    def test_user_is_admin_or_editor_with_sysadmin(self):
        """Test user_is_admin_or_editor with sysadmin user"""
        sysadmin = factories.Sysadmin()

        result = utils.user_is_admin_or_editor(sysadmin['name'])

        assert result is True

    def test_user_is_admin_or_editor_with_admin_membership(self):
        """Test user_is_admin_or_editor with admin membership"""
        user = factories.User()
        org = factories.Organization(users=[{'name': user['name'], 'capacity': 'admin'}])

        result = utils.user_is_admin_or_editor(user['name'])

        assert result is True

    def test_user_is_admin_or_editor_with_editor_membership(self):
        """Test user_is_admin_or_editor with editor membership"""
        user = factories.User()
        org = factories.Organization(users=[{'name': user['name'], 'capacity': 'editor'}])

        result = utils.user_is_admin_or_editor(user['name'])

        assert result is True

    def test_user_is_admin_or_editor_with_member_only(self):
        """Test user_is_admin_or_editor with member-only access"""
        user = factories.User()
        org = factories.Organization(users=[{'name': user['name'], 'capacity': 'member'}])

        result = utils.user_is_admin_or_editor(user['name'])

        assert result is False


class TestMetabaseApiRequests:
    """Test Metabase API request functions"""

    @mock.patch('requests.get')
    def test_metabase_get_request_success(self, mock_get):
        """Test successful Metabase GET request"""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        mock_get.return_value = mock_response

        with mock.patch('ckanext.in_app_reporting.config.metabase_api_key', return_value='test-key'):
            result = utils.metabase_get_request('https://example.com/api/test')

        assert result == {'data': 'test'}
        mock_get.assert_called_once_with(
            'https://example.com/api/test',
            headers={'x-api-key': 'test-key'}
        )

    @mock.patch('requests.get')
    def test_metabase_get_request_failure(self, mock_get):
        """Test failed Metabase GET request"""
        mock_response = mock.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with mock.patch('ckanext.in_app_reporting.config.metabase_api_key', return_value='test-key'):
            result = utils.metabase_get_request('https://example.com/api/test')

        assert result is None

    @mock.patch('requests.get')
    def test_metabase_get_request_exception(self, mock_get):
        """Test Metabase GET request with exception"""
        mock_get.side_effect = Exception('Network error')

        with mock.patch('ckanext.in_app_reporting.config.metabase_api_key', return_value='test-key'):
            result = utils.metabase_get_request('https://example.com/api/test')

        assert result is None

    @mock.patch('requests.post')
    def test_metabase_post_request_success(self, mock_post):
        """Test successful Metabase POST request"""
        mock_response = mock.Mock()
        mock_response.json.return_value = {'id': 123}
        mock_post.return_value = mock_response

        data = {'name': 'test'}

        with mock.patch('ckanext.in_app_reporting.config.metabase_api_key', return_value='test-key'):
            result = utils.metabase_post_request('https://example.com/api/test', data)

        assert result == {'id': 123}
        mock_post.assert_called_once_with(
            'https://example.com/api/test',
            headers={'x-api-key': 'test-key', 'Content-Type': 'application/json'},
            data=json.dumps(data)
        )

    @mock.patch('requests.post')
    def test_metabase_post_request_exception(self, mock_post):
        """Test Metabase POST request with exception"""
        mock_post.side_effect = Exception('Network error')

        data = {'name': 'test'}

        with mock.patch('ckanext.in_app_reporting.config.metabase_api_key', return_value='test-key'):
            result = utils.metabase_post_request('https://example.com/api/test', data)

        assert result is None


class TestUtilityHelpers:
    """Test utility helper functions"""

    def test_split_fullname_with_multiple_names(self):
        """Test split_fullname with multiple names"""
        first, last = utils.split_fullname('John Michael Doe')

        assert first == 'John'
        assert last == 'Doe'

    def test_split_fullname_with_two_names(self):
        """Test split_fullname with two names"""
        first, last = utils.split_fullname('John Doe')

        assert first == 'John'
        assert last == 'Doe'

    def test_split_fullname_with_single_name(self):
        """Test split_fullname with single name"""
        first, last = utils.split_fullname('John')

        assert first is None
        assert last is None

    def test_split_fullname_with_empty_string(self):
        """Test split_fullname with empty string"""
        first, last = utils.split_fullname('')

        assert first is None
        assert last is None

    def test_split_fullname_with_none(self):
        """Test split_fullname with None"""
        first, last = utils.split_fullname(None)

        assert first is None
        assert last is None


class TestMetabaseIframeUrl:
    """Test Metabase iframe URL generation"""

    @mock.patch('time.time', return_value=1234567890)
    @mock.patch('jwt.encode')
    def test_get_metabase_iframe_url_with_jwt(self, mock_jwt_encode, mock_time):
        """Test iframe URL generation with JWT encoding"""
        mock_jwt_encode.return_value = 'test-jwt-token'

        with mock.patch('ckanext.in_app_reporting.config.metabase_site_url', return_value='https://example.com'), \
             mock.patch('ckanext.in_app_reporting.config.metabase_manage_service_url', return_value=None), \
             mock.patch('ckanext.in_app_reporting.config.metabase_embedding_secret_key', return_value='embedding-secret-key'):
    
            result = utils.get_metabase_iframe_url('card', '123', True, True, True)

        expected_url = 'https://example.com/embed/card/test-jwt-token#bordered=true&titled=true&downloads=true'
        assert result == expected_url

        mock_jwt_encode.assert_called_once_with({
            'resource': {'card': '123'},
            'params': {},
            'exp': 1234567890 + (60 * 10)
        }, 'embedding-secret-key', algorithm='HS256')


class TestMetabaseUserToken:
    """Test Metabase user token generation"""

    @mock.patch('time.time', return_value=1234567890)
    @mock.patch('jwt.encode')
    def test_get_metabase_user_token_with_jwt(self, mock_jwt_encode, mock_time):
        """Test user token generation with JWT encoding"""
        test_user = mock.Mock()
        test_user.id = '1234abcd-1234-abcd-1234-abcd1234abcd'
        test_user.name = 'jdoe@example.com'
        test_user.fullname = 'John Doe'

        mock_jwt_encode.return_value = 'user-jwt-token'

        with mock.patch('ckanext.in_app_reporting.config.metabase_manage_service_url', return_value=None), \
             mock.patch('ckanext.in_app_reporting.config.metabase_jwt_shared_secret', return_value='jwt-shared-secret'), \
             mock.patch('ckanext.in_app_reporting.config.group_ids', return_value=['group1', 'group2']), \
             mock.patch('ckanext.in_app_reporting.config.collection_ids', return_value=['1', '2']), \
             mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
     
            mock_get_action.return_value.side_effect = toolkit.ObjectNotFound()
     
            result = utils.get_metabase_user_token(test_user)

        assert result == 'user-jwt-token'

        mock_jwt_encode.assert_called_once_with({
            'email': 'jdoe@example.com',
            'exp': 1234567890 + (60 * 10),
            'groups': ['group1', 'group2'],
            'first_name': 'John',
            'last_name': 'Doe'
        }, 'jwt-shared-secret', algorithm='HS256')

    def test_get_metabase_user_token_with_mapping(self, metabase_mapping_factory):
        """Test user token generation with existing mapping"""
        user = factories.User()
        mapping = metabase_mapping_factory(user_id=user['id'])

        with mock.patch('ckanext.in_app_reporting.config.metabase_manage_service_url', return_value=None), \
             mock.patch('ckanext.in_app_reporting.config.metabase_jwt_shared_secret', return_value='jwt-shared-secret'), \
             mock.patch('jwt.encode', return_value='mapped-token'), \
             mock.patch('time.time', return_value=1234567890), \
             mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
    
            mock_get_action.return_value.return_value = {
                'platform_uuid': mapping.platform_uuid,
                'group_ids': ['group1', 'group2'],
                'collection_ids': ['1', '2']
            }
    
            result = utils.get_metabase_user_token(mock.Mock(id=user['id'], name=user['name'], fullname=None))

        assert result == 'mapped-token'


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestMetabaseHelpers:
    """Test Metabase helper functions"""

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_embeddable_success(self, mock_get_request):
        """Test get_metabase_embeddable with successful response"""
        mock_get_request.return_value = [
            {'id': 1, 'name': 'Card 1'},
            {'id': 2, 'name': 'Card 2'}
        ]

        with mock.patch('ckanext.in_app_reporting.config.metabase_site_url', return_value='https://example.com'):
            result = utils.get_metabase_embeddable('card')

        assert result == [1, 2]
        mock_get_request.assert_called_once_with('https://example.com/api/card/embeddable')

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_embeddable_invalid_type(self, mock_get_request):
        """Test get_metabase_embeddable with invalid model type"""
        result = utils.get_metabase_embeddable('invalid')

        assert result == []
        mock_get_request.assert_not_called()

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_embeddable_no_response(self, mock_get_request):
        """Test get_metabase_embeddable with no response"""
        mock_get_request.return_value = None

        with mock.patch('ckanext.in_app_reporting.config.metabase_site_url', return_value='https://example.com'):
            result = utils.get_metabase_embeddable('dashboard')

        assert result == []

    def test_get_metabase_collection_id_with_collections(self):
        """Test get_metabase_collection_id with collections configured"""
        with mock.patch('ckanext.in_app_reporting.config.collection_ids', return_value=['1', '2', '3']):
            result = utils.get_metabase_collection_id()

        assert result == '1'

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_table_id_success(self, mock_get_request):
        """Test get_metabase_table_id with successful response"""
        mock_get_request.return_value = {
            'tables': [
                {'id': 1, 'name': 'table1'},
                {'id': 2, 'name': 'table2'},
                {'id': 3, 'name': 'target_table'}
            ]
        }

        with mock.patch('ckanext.in_app_reporting.config.metabase_site_url', return_value='https://example.com'), \
             mock.patch('ckanext.in_app_reporting.config.metabase_db_id', return_value='4'):
            result = utils.get_metabase_table_id('target_table')

        assert result == 3
        mock_get_request.assert_called_once_with('https://example.com/api/database/4?include=tables')

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_table_id_not_found(self, mock_get_request):
        """Test get_metabase_table_id when table not found"""
        mock_get_request.return_value = {
            'tables': [
                {'id': 1, 'name': 'table1'},
                {'id': 2, 'name': 'table2'}
            ]
        }

        with mock.patch('ckanext.in_app_reporting.config.metabase_site_url', return_value='https://example.com'), \
             mock.patch('ckanext.in_app_reporting.config.metabase_db_id', return_value='1'):
            result = utils.get_metabase_table_id('nonexistent_table')

        assert result is None

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_model_id_success(self, mock_get_request):
        """Test get_metabase_model_id with successful response"""
        mock_get_request.return_value = [
            {'id': 1, 'type': 'question'},
            {'id': 2, 'type': 'model'},
            {'id': 3, 'type': 'question'}
        ]

        with mock.patch('ckanext.in_app_reporting.config.metabase_site_url', return_value='https://example.com'):
            result = utils.get_metabase_model_id('123')

        assert result == 2
        mock_get_request.assert_called_once_with('https://example.com/api/card?f=table&model_id=123')

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_model_id_no_model(self, mock_get_request):
        """Test get_metabase_model_id when no model found"""
        mock_get_request.return_value = [
            {'id': 1, 'type': 'question'},
            {'id': 2, 'type': 'question'}
        ]

        with mock.patch('ckanext.in_app_reporting.config.metabase_site_url', return_value='https://example.com'):
            result = utils.get_metabase_model_id('123')

        assert result == ''

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_cards_by_table_id_filters_and_sorts(self, mock_get_request):
        mock_get_request.return_value = [
            {'id': 1, 'name': 'B', 'type': 'model', 'updated_at': '2025-08-01T18:20:49.005658Z', 'collection_id': 3},
            {'id': 2, 'name': 'A', 'type': 'question', 'updated_at': '2025-08-02T18:20:49.005658Z', 'collection_id': 1},
            {'id': 3, 'name': 'C', 'type': 'model', 'updated_at': '2025-08-03T18:20:49.005658Z', 'collection_id': 1}
        ]
        with mock.patch('ckanext.in_app_reporting.utils.METABASE_SITE_URL', 'https://example.com'):
            result = utils.get_metabase_cards_by_table_id('793')

        mock_get_request.assert_called_once_with('https://example.com/api/card?f=table&model_id=793')
        assert result == [
            {'id': 3, 'name': 'C', 'type': 'model', 'updated_at': '2025-08-03T18:20:49.005658Z'},
            {'id': 2, 'name': 'A', 'type': 'question', 'updated_at': '2025-08-02T18:20:49.005658Z'}
        ]

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_sql_questions_filters(self, mock_get_request):
        """Test get_metabase_sql_questions with filters"""
        mock_get_request.return_value = [
            {
                'id': 1,
                'name': 'Resource 1',
                'type': 'question',
                'updated_at': '2025-08-01T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': None,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT "Golf Course", sum("Rounds") as "Rounds" FROM "0829999d-80a1-4207-a921-66796079a05e" GROUP BY 1'
                    }
                }
            },
            {
                'id': 2,
                'name': 'Resource 2',
                'type': 'question',
                'updated_at': '2025-08-02T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': 99,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT "Golf Course", SUM("Rounds") as "Sum" FROM "0829999d-80a1-4207-a921-66796079a05e" GROUP BY "Golf Course"'
                    }
                }
            },
            {
                'id': 3,
                'name': 'Resource 3',
                'type': 'question',
                'updated_at': '2025-08-03T18:20:49.005658Z',
                'collection_id': 3,
                'table_id': 99,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT "Council", COUNT(distinct "Project Name") as "Count" FROM "7bd0b918-0559-4fa2-a642-fee6793eb854" GROUP BY "Council"'
                    }
                }
            }
        ]
        with mock.patch('ckanext.in_app_reporting.utils.METABASE_DB_ID', '4'), \
             mock.patch('ckanext.in_app_reporting.utils.METABASE_SITE_URL', 'https://example.com'):
            result = utils.get_metabase_sql_questions('0829999d-80a1-4207-a921-66796079a05e')

        mock_get_request.assert_called_once_with('https://example.com/api/card?f=database&model_id=4')
        assert result == [
            {'id': 1, 'name': 'Resource 1', 'type': 'question', 'updated_at': '2025-08-01T18:20:49.005658Z'}
        ]


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestMetabaseMappingUtils:
    """Test Metabase mapping utility functions"""

    def test_metabase_mapping_create_success(self):
        """Test successful metabase mapping creation"""
        user = factories.User()

        data_dict = {
            'user_id': user['id'],
            'platform_uuid': '12345678-1234-1234-1234-123456789012',
            'group_ids': ['group1', 'group2'],
            'collection_ids': ['1', '2']
        }

        result = utils.metabase_mapping_create(data_dict)

        assert result['user_id'] == user['id']
        assert result['platform_uuid'] == '12345678-1234-1234-1234-123456789012'
        assert result['group_ids'] == ['group1', 'group2']
        assert result['collection_ids'] == ['1', '2']
        assert 'created' in result
        assert 'modified' in result

    def test_metabase_mapping_create_missing_user_id(self):
        """Test metabase mapping creation without user ID"""
        data_dict = {}

        with pytest.raises(toolkit.ValidationError) as exc_info:
            utils.metabase_mapping_create(data_dict)

        assert 'User ID is required' in str(exc_info.value)

    def test_metabase_mapping_create_user_not_found(self):
        """Test metabase mapping creation with non-existent user"""
        data_dict = {'user_id': 'non-existent-user-id'}

        with pytest.raises(toolkit.ValidationError) as exc_info:
            utils.metabase_mapping_create(data_dict)

        assert 'User with ID non-existent-user-id not found' in str(exc_info.value)

    def test_metabase_mapping_create_already_exists(self, metabase_mapping_factory):
        """Test metabase mapping creation when mapping already exists"""
        user = factories.User()
        metabase_mapping_factory(user_id=user['id'])

        data_dict = {
            'user_id': user['id'],
            'platform_uuid': '12345678-1234-1234-1234-123456789012'
        }

        with pytest.raises(toolkit.ValidationError) as exc_info:
            utils.metabase_mapping_create(data_dict)

        assert 'Mapping already exists. Use update instead.' in str(exc_info.value)

    def test_metabase_mapping_create_invalid_uuid(self):
        """Test metabase mapping creation with invalid UUID"""
        user = factories.User()

        data_dict = {
            'user_id': user['id'],
            'platform_uuid': 'invalid-uuid'
        }

        with pytest.raises(toolkit.ValidationError) as exc_info:
            utils.metabase_mapping_create(data_dict)

        assert 'OpenGov User UUID must be a valid UUID string' in str(exc_info.value)

    def test_metabase_mapping_update_success(self, metabase_mapping_factory):
        """Test successful metabase mapping update"""
        user = factories.User()
        mapping = metabase_mapping_factory(user_id=user['id'])

        data_dict = {
            'user_id': user['id'],
            'platform_uuid': '87654321-4321-4321-4321-210987654321',
            'group_ids': ['new_group1', 'new_group2'],
            'collection_ids': ['1']
        }

        result = utils.metabase_mapping_update(data_dict)

        assert result['user_id'] == user['id']
        assert result['platform_uuid'] == '87654321-4321-4321-4321-210987654321'
        assert result['group_ids'] == ['new_group1', 'new_group2']
        assert result['collection_ids'] == ['1']

    def test_metabase_mapping_update_not_found(self):
        """Test metabase mapping update when mapping doesn't exist"""
        user = factories.User()

        data_dict = {'user_id': user['id']}

        with pytest.raises(toolkit.ObjectNotFound) as exc_info:
            utils.metabase_mapping_update(data_dict)

        assert f'No mapping found for user_id={user["id"]}' in str(exc_info.value)

    def test_metabase_mapping_delete_success(self, metabase_mapping_factory):
        """Test successful metabase mapping deletion"""
        user = factories.User()
        mapping = metabase_mapping_factory(user_id=user['id'])

        data_dict = {'user_id': user['id']}

        result = utils.metabase_mapping_delete(data_dict)

        assert f'Mapping for user_id {user["id"]} deleted successfully.' in result['message']

    def test_metabase_mapping_delete_not_found(self):
        """Test metabase mapping deletion when mapping doesn't exist"""
        user = factories.User()

        data_dict = {'user_id': user['id']}

        with pytest.raises(toolkit.ObjectNotFound) as exc_info:
            utils.metabase_mapping_delete(data_dict)

        assert f'No mapping found for user_id {user["id"]}' in str(exc_info.value)


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestGetMetabaseChartList:
    """Test get_metabase_chart_list function"""

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_chart_list_with_table_id_match(self, mock_get_request):
        """Test get_metabase_chart_list with cards matching table_id"""
        mock_get_request.return_value = [
            {
                'id': 1,
                'entity_id': 'card-1',
                'name': 'Chart A',
                'type': 'question',
                'updated_at': '2025-08-01T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': 123,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM table_123'
                    }
                }
            },
            {
                'id': 2,
                'entity_id': 'card-2',
                'name': 'Chart B',
                'type': 'question',
                'updated_at': '2025-08-02T18:20:49.005658Z',
                'collection_id': 2,
                'table_id': 456,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM table_456'
                    }
                }
            },
            {
                'id': 3,
                'entity_id': 'card-3',
                'name': 'Chart C',
                'type': 'question',
                'updated_at': '2025-08-03T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': 123,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM table_123'
                    }
                }
            }
        ]

        with mock.patch('ckanext.in_app_reporting.utils.METABASE_SITE_URL', 'https://example.com'), \
             mock.patch('ckanext.in_app_reporting.utils.METABASE_DB_ID', '4'), \
             mock.patch('ckanext.in_app_reporting.utils.collection_ids', ['1', '2']), \
             mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
            
            mock_get_action.return_value.side_effect = toolkit.ObjectNotFound()

            result = utils.get_metabase_chart_list(123, 'resource-123')

        mock_get_request.assert_called_once_with('https://example.com/api/card?f=database&model_id=4')
        assert len(result) == 2
        assert result[0]['id'] == 3  # Sorted by updated_at desc, then name
        assert result[0]['name'] == 'Chart C'
        assert result[1]['id'] == 1
        assert result[1]['name'] == 'Chart A'

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_chart_list_with_resource_id_match(self, mock_get_request):
        """Test get_metabase_chart_list with cards matching resource_id in SQL query"""
        mock_get_request.return_value = [
            {
                'id': 1,
                'entity_id': 'card-1',
                'name': 'SQL Chart A',
                'type': 'question',
                'updated_at': '2025-08-01T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': None,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM "resource-123" WHERE status = "active"'
                    }
                }
            },
            {
                'id': 2,
                'entity_id': 'card-2',
                'name': 'SQL Chart B',
                'type': 'question',
                'updated_at': '2025-08-02T18:20:49.005658Z',
                'collection_id': 2,
                'table_id': None,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM "resource-456" WHERE status = "active"'
                    }
                }
            },
            {
                'id': 3,
                'entity_id': 'card-3',
                'name': 'SQL Chart C',
                'type': 'question',
                'updated_at': '2025-08-03T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': None,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT COUNT(*) FROM "resource-123" GROUP BY category'
                    }
                }
            }
        ]

        with mock.patch('ckanext.in_app_reporting.utils.METABASE_SITE_URL', 'https://example.com'), \
             mock.patch('ckanext.in_app_reporting.utils.METABASE_DB_ID', '4'), \
             mock.patch('ckanext.in_app_reporting.utils.collection_ids', ['1', '2']), \
             mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
            
            mock_get_action.return_value.side_effect = toolkit.ObjectNotFound()

            result = utils.get_metabase_chart_list(123, 'resource-123')

        mock_get_request.assert_called_once_with('https://example.com/api/card?f=database&model_id=4')
        assert len(result) == 2
        assert result[0]['id'] == 3  # Sorted by updated_at desc, then name
        assert result[0]['name'] == 'SQL Chart C'
        assert result[1]['id'] == 1
        assert result[1]['name'] == 'SQL Chart A'

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_chart_list_no_api_response(self, mock_get_request):
        """Test get_metabase_chart_list when API returns no response"""
        mock_get_request.return_value = None

        with mock.patch('ckanext.in_app_reporting.utils.METABASE_SITE_URL', 'https://example.com'), \
             mock.patch('ckanext.in_app_reporting.utils.METABASE_DB_ID', '4'), \
             mock.patch('ckanext.in_app_reporting.utils.collection_ids', ['1', '2']), \
             mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
            
            mock_get_action.return_value.side_effect = toolkit.ObjectNotFound()

            result = utils.get_metabase_chart_list(123, 'resource-123')

        mock_get_request.assert_called_once_with('https://example.com/api/card?f=database&model_id=4')
        assert result == []

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_chart_list_empty_response(self, mock_get_request):
        """Test get_metabase_chart_list when API returns empty list"""
        mock_get_request.return_value = []

        with mock.patch('ckanext.in_app_reporting.utils.METABASE_SITE_URL', 'https://example.com'), \
             mock.patch('ckanext.in_app_reporting.utils.METABASE_DB_ID', '4'), \
             mock.patch('ckanext.in_app_reporting.utils.collection_ids', ['1', '2']), \
             mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
            
            mock_get_action.return_value.side_effect = toolkit.ObjectNotFound()

            result = utils.get_metabase_chart_list(123, 'resource-123')

        mock_get_request.assert_called_once_with('https://example.com/api/card?f=database&model_id=4')
        assert result == []

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_chart_list_filters_by_collection_and_type(self, mock_get_request):
        """Test get_metabase_chart_list filters by collection_id and type='question'"""
        mock_get_request.return_value = [
            {
                'id': 1,
                'entity_id': 'card-1',
                'name': 'Question Chart',
                'type': 'question',
                'updated_at': '2025-08-01T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': 123,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM table_123'
                    }
                }
            },
            {
                'id': 2,
                'entity_id': 'card-2',
                'name': 'Model Chart',
                'type': 'model',  # Should be filtered out
                'updated_at': '2025-08-02T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': 123,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM table_123'
                    }
                }
            },
            {
                'id': 3,
                'entity_id': 'card-3',
                'name': 'Other Collection Chart',
                'type': 'question',
                'updated_at': '2025-08-03T18:20:49.005658Z',
                'collection_id': 3,  # Not in allowed collections
                'table_id': 123,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM table_123'
                    }
                }
            }
        ]

        with mock.patch('ckanext.in_app_reporting.utils.METABASE_SITE_URL', 'https://example.com'), \
             mock.patch('ckanext.in_app_reporting.utils.METABASE_DB_ID', '4'), \
             mock.patch('ckanext.in_app_reporting.utils.collection_ids', ['1', '2']), \
             mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
            
            mock_get_action.return_value.side_effect = toolkit.ObjectNotFound()

            result = utils.get_metabase_chart_list(123, 'resource-123')

        mock_get_request.assert_called_once_with('https://example.com/api/card?f=database&model_id=4')
        assert len(result) == 1
        assert result[0]['id'] == 1
        assert result[0]['name'] == 'Question Chart'
        assert result[0]['type'] == 'question'

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_chart_list_sorts_by_updated_at_and_name(self, mock_get_request):
        """Test get_metabase_chart_list sorts by updated_at desc, then name"""
        mock_get_request.return_value = [
            {
                'id': 1,
                'entity_id': 'card-1',
                'name': 'Z Chart',
                'type': 'question',
                'updated_at': '2025-08-01T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': 123,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM table_123'
                    }
                }
            },
            {
                'id': 2,
                'entity_id': 'card-2',
                'name': 'A Chart',
                'type': 'question',
                'updated_at': '2025-08-03T18:20:48.004547Z',  # Most recent
                'collection_id': 1,
                'table_id': 123,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM table_123'
                    }
                }
            },
            {
                'id': 3,
                'entity_id': 'card-3',
                'name': 'B Chart',
                'type': 'question',
                'updated_at': '2025-08-03T18:20:30.005658Z',  # After card 2
                'collection_id': 1,
                'table_id': 123,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM table_123'
                    }
                }
            }
        ]

        with mock.patch('ckanext.in_app_reporting.utils.METABASE_SITE_URL', 'https://example.com'), \
             mock.patch('ckanext.in_app_reporting.utils.METABASE_DB_ID', '4'), \
             mock.patch('ckanext.in_app_reporting.utils.collection_ids', ['1', '2']), \
             mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
            
            mock_get_action.return_value.side_effect = toolkit.ObjectNotFound()

            result = utils.get_metabase_chart_list(123, 'resource-123')

        mock_get_request.assert_called_once_with('https://example.com/api/card?f=database&model_id=4')
        assert len(result) == 3
        # Should be sorted by updated_at desc, then name asc
        assert result[0]['id'] == 2  # Most recent, name 'A Chart'
        assert result[1]['id'] == 3  # Same time, name 'B Chart'
        assert result[2]['id'] == 1  # Older time, name 'Z Chart'

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_chart_list_mixed_table_and_sql_matches(self, mock_get_request):
        """Test get_metabase_chart_list with both table_id and resource_id matches"""
        mock_get_request.return_value = [
            {
                'id': 1,
                'entity_id': 'card-1',
                'name': 'Table Match Chart',
                'type': 'question',
                'updated_at': '2025-08-01T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': 123,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM table_123'
                    }
                }
            },
            {
                'id': 2,
                'entity_id': 'card-2',
                'name': 'SQL Match Chart',
                'type': 'question',
                'updated_at': '2025-08-02T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': None,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM "resource-123" WHERE status = "active"'
                    }
                }
            },
            {
                'id': 3,
                'entity_id': 'card-3',
                'name': 'No Match Chart',
                'type': 'question',
                'updated_at': '2025-08-03T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': 456,  # Different table_id
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM "resource-456" WHERE status = "active"'  # Different resource
                    }
                }
            }
        ]

        with mock.patch('ckanext.in_app_reporting.utils.METABASE_SITE_URL', 'https://example.com'), \
             mock.patch('ckanext.in_app_reporting.utils.METABASE_DB_ID', '4'), \
             mock.patch('ckanext.in_app_reporting.utils.collection_ids', ['1', '2']), \
             mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
            
            mock_get_action.return_value.side_effect = toolkit.ObjectNotFound()

            result = utils.get_metabase_chart_list(123, 'resource-123')

        mock_get_request.assert_called_once_with('https://example.com/api/card?f=database&model_id=4')
        assert len(result) == 2
        # Should be sorted by updated_at desc, then name asc
        assert result[0]['id'] == 2  # SQL Match Chart
        assert result[0]['name'] == 'SQL Match Chart'
        assert result[1]['id'] == 1  # Table Match Chart
        assert result[1]['name'] == 'Table Match Chart'

    @mock.patch('ckanext.in_app_reporting.utils.metabase_get_request')
    def test_get_metabase_chart_list_includes_text_field(self, mock_get_request):
        """Test get_metabase_chart_list includes 'text' field in returned cards"""
        mock_get_request.return_value = [
            {
                'id': 1,
                'entity_id': 'card-1',
                'name': 'Test Chart',
                'type': 'question',
                'updated_at': '2025-08-01T18:20:49.005658Z',
                'collection_id': 1,
                'table_id': 123,
                'dataset_query': {
                    'native': {
                        'query': 'SELECT * FROM table_123'
                    }
                }
            }
        ]

        with mock.patch('ckanext.in_app_reporting.utils.METABASE_SITE_URL', 'https://example.com'), \
             mock.patch('ckanext.in_app_reporting.utils.METABASE_DB_ID', '4'), \
             mock.patch('ckanext.in_app_reporting.utils.collection_ids', ['1', '2']), \
             mock.patch('ckan.plugins.toolkit.get_action') as mock_get_action:
            
            mock_get_action.return_value.side_effect = toolkit.ObjectNotFound()

            result = utils.get_metabase_chart_list(123, 'resource-123')

        mock_get_request.assert_called_once_with('https://example.com/api/card?f=database&model_id=4')
        assert len(result) == 1
        assert result[0]['text'] == 'Test Chart'  # Should include text field
        assert result[0]['name'] == 'Test Chart'
