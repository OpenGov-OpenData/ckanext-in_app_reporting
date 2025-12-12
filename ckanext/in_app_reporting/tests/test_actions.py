"""
Tests for action.py functions.
"""
import pytest
from unittest import mock
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories
from ckan.tests.helpers import call_action

import ckanext.in_app_reporting.action as action


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestMetabaseMappingActions:
    """Test metabase mapping CRUD actions"""

    def test_metabase_mapping_create_success(self, mock_metabase_config):
        """Test successful creation of metabase mapping"""
        user = factories.User()

        with mock.patch('ckanext.in_app_reporting.utils.metabase_mapping_create') as mock_create:
            mock_create.return_value = {
                'user_id': user['id'],
                'platform_uuid': '12345678-1234-1234-1234-123456789012',
                'email': user['email']
            }
    
            context = {'user': user['name']}
            data_dict = {
                'user_id': user['id'],
                'platform_uuid': '12345678-1234-1234-1234-123456789012'
            }
    
            with mock.patch('ckan.plugins.toolkit.check_access'):
                result = call_action('metabase_mapping_create', context, **data_dict)
    
            assert result['user_id'] == user['id']
            assert result['platform_uuid'] == '12345678-1234-1234-1234-123456789012'
            mock_create.assert_called_once_with(data_dict)

    def test_metabase_mapping_create_validation_error(self, mock_metabase_config):
        """Test metabase mapping creation with validation error"""
        user = factories.User()

        with mock.patch('ckanext.in_app_reporting.utils.metabase_mapping_create') as mock_create:
            mock_create.side_effect = Exception('Invalid data')
    
            context = {'user': user['name']}
            data_dict = {'user_id': user['id']}
    
            with mock.patch('ckan.plugins.toolkit.check_access'), \
                 pytest.raises(toolkit.ValidationError) as exc_info:
                call_action('metabase_mapping_create', context, **data_dict)
    
            assert 'Invalid data' in str(exc_info.value)

    def test_metabase_mapping_update_success(self, mock_metabase_config):
        """Test successful update of metabase mapping"""
        user = factories.User()

        with mock.patch('ckanext.in_app_reporting.utils.metabase_mapping_update') as mock_update:
            mock_update.return_value = {
                'user_id': user['id'],
                'platform_uuid': '12345678-1234-1234-1234-123456789012',
                'email': user['email']
            }
    
            context = {'user': user['name']}
            data_dict = {
                'user_id': user['id'],
                'platform_uuid': '12345678-1234-1234-1234-123456789012'
            }
    
            with mock.patch('ckan.plugins.toolkit.check_access'):
                result = call_action('metabase_mapping_update', context, **data_dict)
    
            assert result['user_id'] == user['id']
            mock_update.assert_called_once_with(data_dict)

    def test_metabase_mapping_delete_success(self, mock_metabase_config):
        """Test successful deletion of metabase mapping"""
        user = factories.User()

        with mock.patch('ckanext.in_app_reporting.utils.metabase_mapping_delete') as mock_delete:
            mock_delete.return_value = {'message': 'Mapping deleted successfully'}
    
            context = {'user': user['name']}
            data_dict = {'user_id': user['id']}
    
            with mock.patch('ckan.plugins.toolkit.check_access'):
                result = call_action('metabase_mapping_delete', context, **data_dict)
    
            assert 'message' in result
            mock_delete.assert_called_once_with(data_dict)

    def test_metabase_mapping_show_with_user_id(self, metabase_mapping_factory):
        """Test showing metabase mapping by user_id"""
        user = factories.User()
        mapping = metabase_mapping_factory(user_id=user['id'])

        context = {'user': user['name']}
        data_dict = {'user_id': user['id']}

        with mock.patch('ckan.plugins.toolkit.check_access'):
            result = call_action('metabase_mapping_show', context, **data_dict)

        assert result['user_id'] == user['id']
        assert result['email'] == mapping.email
        assert isinstance(result['group_ids'], list)
        assert isinstance(result['collection_ids'], list)

    def test_metabase_mapping_show_with_email(self, metabase_mapping_factory):
        """Test showing metabase mapping by email"""
        user = factories.User()
        mapping = metabase_mapping_factory(user_id=user['id'], email=user['email'])

        context = {'user': user['name']}
        data_dict = {'email': user['email']}

        with mock.patch('ckan.plugins.toolkit.check_access'):
            result = call_action('metabase_mapping_show', context, **data_dict)

        assert result['user_id'] == user['id']
        assert result['email'] == user['email']

    def test_metabase_mapping_show_validation_error(self):
        """Test metabase mapping show without user_id or email"""
        user = factories.User()

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_mapping_show', context, **data_dict)

        assert 'Provide either user id or email' in str(exc_info.value)

    def test_metabase_mapping_show_not_found(self):
        """Test metabase mapping show when mapping doesn't exist"""
        user = factories.User()

        context = {'user': user['name']}
        data_dict = {'user_id': user['id']}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ObjectNotFound) as exc_info:
            call_action('metabase_mapping_show', context, **data_dict)

        assert 'Metabase mapping not found' in str(exc_info.value)

    def test_metabase_mapping_list(self, metabase_mapping_factory):
        """Test listing all metabase mappings"""
        user1 = factories.User()
        user2 = factories.User()
        metabase_mapping_factory(user_id=user1['id'])
        metabase_mapping_factory(user_id=user2['id'])

        context = {'user': user1['name']}

        with mock.patch('ckan.plugins.toolkit.check_access'):
            result = call_action('metabase_mapping_list', context)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all('user_id' in mapping for mapping in result)
        assert all('email' in mapping for mapping in result)


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestMetabaseCardPublish:
    """Test metabase card publishing actions"""

    def test_metabase_card_publish_success(self, mock_requests, mock_metabase_config):
        """Test successful card publishing"""
        user = factories.User()
        mock_requests['put'].return_value.status_code = 200

        context = {'user': user['name']}
        data_dict = {'id': '123'}

        with mock.patch('ckan.plugins.toolkit.check_access'):
            result = call_action('metabase_card_publish', context, **data_dict)

        assert result['success'] is True
        mock_requests['put'].assert_called_once()

    def test_metabase_card_publish_missing_id(self, mock_metabase_config):
        """Test card publishing without card ID"""
        user = factories.User()

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_card_publish', context, **data_dict)

        assert 'Card ID Required' in str(exc_info.value)

    def test_metabase_card_publish_api_failure(self, mock_requests, mock_metabase_config):
        """Test card publishing with API failure"""
        user = factories.User()
        mock_requests['put'].return_value.status_code = 400

        context = {'user': user['name']}
        data_dict = {'id': '123'}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_card_publish', context, **data_dict)

        assert 'Failed to publish card' in str(exc_info.value)


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestMetabaseDashboardPublish:
    """Test metabase dashboard publishing actions"""

    def test_metabase_dashboard_publish_success(self, mock_requests, mock_metabase_config):
        """Test successful dashboard publishing"""
        user = factories.User()
        mock_requests['put'].return_value.status_code = 200

        context = {'user': user['name']}
        data_dict = {'id': '123'}

        with mock.patch('ckan.plugins.toolkit.check_access'):
            result = call_action('metabase_dashboard_publish', context, **data_dict)

        assert result['success'] is True
        mock_requests['put'].assert_called_once()

    def test_metabase_dashboard_publish_with_params(self, mock_requests, mock_metabase_config):
        """Test dashboard publishing with parameters enabled"""
        user = factories.User()
        mock_requests['put'].return_value.status_code = 200
        mock_requests['get'].return_value.json.return_value = {
            'parameters': [
                {'slug': 'param1'},
                {'slug': 'param2'}
            ]
        }

        context = {'user': user['name']}
        data_dict = {'id': '123', 'enable_params': True}

        with mock.patch('ckan.plugins.toolkit.check_access'):
            result = call_action('metabase_dashboard_publish', context, **data_dict)

        assert result['success'] is True
        mock_requests['get'].assert_called_once()
        mock_requests['put'].assert_called_once()

    def test_metabase_dashboard_publish_missing_id(self, mock_metabase_config):
        """Test dashboard publishing without dashboard ID"""
        user = factories.User()

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_dashboard_publish', context, **data_dict)

        assert 'Dashboard ID Required' in str(exc_info.value)


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestMetabaseModelCreate:
    """Test metabase model creation actions"""

    def test_metabase_model_create_success(self, mock_requests, mock_metabase_config):
        """Test successful model creation"""
        user = factories.User()
        resource = factories.Resource()

        # Mock search results
        mock_requests['get'].return_value.json.side_effect = [
            # Search results
            {
                'data': [{
                    'table_name': resource['id'],
                    'table_id': 123
                }]
            },
            # Query metadata
            {
                'fields': [
                    {'id': 1, 'name': 'field1', 'base_type': 'type::Text'},
                    {'id': 2, 'name': '_full_text', 'base_type': 'type::Text'},  # Should be filtered out
                    {'id': 3, 'name': 'field2', 'base_type': 'type::Integer'}
                ]
            }
        ]

        # Mock post response
        mock_requests['post'].return_value.json.return_value = {'id': 456, 'success': True}

        context = {'user': user['name']}
        data_dict = {
            'resource_id': resource['id'],
            'name': 'Test Model',
            'description': 'Test Description'
        }

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.utils.metabase_get_request', side_effect=mock_requests['get'].return_value.json.side_effect), \
             mock.patch('ckanext.in_app_reporting.utils.metabase_post_request', return_value={'id': 456, 'success': True}):
            result = call_action('metabase_model_create', context, **data_dict)

        assert result['id'] == 456
        assert result['success'] is True

    def test_metabase_model_create_missing_resource_id(self, mock_metabase_config):
        """Test model creation without resource ID"""
        user = factories.User()

        context = {'user': user['name']}
        data_dict = {'name': 'Test Model'}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_model_create', context, **data_dict)

        assert 'Resource ID required' in str(exc_info.value)

    def test_metabase_model_create_missing_name(self, mock_metabase_config):
        """Test model creation without model name"""
        user = factories.User()
        resource = factories.Resource()

        context = {'user': user['name']}
        data_dict = {'resource_id': resource['id']}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_model_create', context, **data_dict)

        assert 'Model name required' in str(exc_info.value)

    def test_metabase_model_create_resource_not_found(self, mock_metabase_config):
        """Test model creation with non-existent resource"""
        user = factories.User()

        context = {'user': user['name']}
        data_dict = {
            'resource_id': 'non-existent-resource',
            'name': 'Test Model'
        }

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_model_create', context, **data_dict)

        assert 'Resource not found' in str(exc_info.value)

    def test_metabase_model_create_table_not_found_in_metabase(self, mock_requests, mock_metabase_config):
        """Test model creation when table not found in Metabase"""
        user = factories.User()
        resource = factories.Resource()

        mock_requests['get'].return_value.json.return_value = {'data': []}

        context = {'user': user['name']}
        data_dict = {
            'resource_id': resource['id'],
            'name': 'Test Model'
        }

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.utils.metabase_get_request', return_value={'data': []}), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_model_create', context, **data_dict)

        assert 'Failed to find matching table for resource in Metabase' in str(exc_info.value)


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestMetabaseSqlQuestionsList:
    """Test metabase SQL questions listing"""

    def test_metabase_sql_questions_list_success(self, mock_metabase_config):
        """Test successful SQL questions listing"""
        user = factories.User()
        resource = factories.Resource()

        expected_questions = [
            {'id': 1, 'name': 'Question 1', 'type': 'question'},
            {'id': 2, 'name': 'Question 2', 'type': 'question'}
        ]

        context = {'user': user['name']}
        data_dict = {'resource_id': resource['id']}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.utils.get_metabase_sql_questions', return_value=expected_questions):
            result = call_action('metabase_sql_questions_list', context, **data_dict)

        assert result == expected_questions

    def test_metabase_sql_questions_list_no_questions(self, mock_metabase_config):
        """Test SQL questions listing when no questions found"""
        user = factories.User()
        resource = factories.Resource()

        context = {'user': user['name']}
        data_dict = {'resource_id': resource['id']}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.utils.get_metabase_sql_questions', return_value=None):
            result = call_action('metabase_sql_questions_list', context, **data_dict)

        assert result == []

    def test_metabase_sql_questions_list_missing_resource_id(self, mock_metabase_config):
        """Test SQL questions listing without resource ID"""
        user = factories.User()

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_sql_questions_list', context, **data_dict)

        assert 'Resource ID required' in str(exc_info.value)

    def test_metabase_sql_questions_list_invalid_resource_id(self, mock_metabase_config):
        """Test SQL questions listing with invalid resource ID type"""
        user = factories.User()

        context = {'user': user['name']}
        data_dict = {'resource_id': 123}  # Should be string

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_sql_questions_list', context, **data_dict)

        assert 'Resource ID required' in str(exc_info.value)


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestMetabaseUserCreatedCardsList:
    """Test metabase user created cards listing actions"""

    def test_metabase_user_created_cards_list_with_email(self, mock_metabase_config):
        """Test listing cards with email parameter"""
        user = factories.User(email='test@example.com')
        expected_cards = [
            {
                'id': 1,
                'name': 'Test Card 1',
                'description': 'Description 1',
                'type': 'question',
                'display': 'bar',
                'created_at': None,
                'updated_at': None,
                'creator_id': 123
            },
            {
                'id': 2,
                'name': 'Test Card 2',
                'description': 'Description 2',
                'type': 'question',
                'display': 'line',
                'created_at': None,
                'updated_at': None,
                'creator_id': 123
            }
        ]

        context = {'user': user['name']}
        data_dict = {'email': 'test@example.com'}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.utils.get_metabase_user_created_cards', return_value=expected_cards):
            result = call_action('metabase_user_created_cards_list', context, **data_dict)

        assert result == expected_cards
        assert len(result) == 2

    def test_metabase_user_created_cards_list_without_email(self, mock_metabase_config):
        """Test listing cards using current user's email"""
        user = factories.User(email='test@example.com')
        expected_cards = [
            {
                'id': 1,
                'name': 'Test Card',
                'description': 'Description',
                'type': 'question',
                'display': 'bar',
                'created_at': None,
                'updated_at': None,
                'creator_id': 123
            }
        ]

        # Create a mock user object
        mock_user_obj = mock.Mock()
        mock_user_obj.email = user.get('email')
        mock_user_obj.name = user['name']

        context = {
            'user': user['name'],
            'auth_user_obj': mock_user_obj
        }
        data_dict = {}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.utils.get_metabase_user_created_cards', return_value=expected_cards):
            result = call_action('metabase_user_created_cards_list', context, **data_dict)

        assert result == expected_cards

    def test_metabase_user_created_cards_list_no_cards(self, mock_metabase_config):
        """Test listing cards when no cards found"""
        user = factories.User(email='test@example.com')

        context = {'user': user['name']}
        data_dict = {'email': 'test@example.com'}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.utils.get_metabase_user_created_cards', return_value=[]):
            result = call_action('metabase_user_created_cards_list', context, **data_dict)

        assert result == []

    def test_metabase_user_created_cards_list_not_authenticated(self, mock_metabase_config):
        """Test listing cards when user is not authenticated"""
        # Set auth_user_obj to None explicitly in context
        context = {'auth_user_obj': None}
        data_dict = {}

        # Mock tk.g.userobj to return None without requiring app context
        mock_g = mock.MagicMock()
        mock_g.userobj = None

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.action.tk.g', mock_g):
            with pytest.raises(toolkit.NotAuthorized) as exc_info:
                call_action('metabase_user_created_cards_list', context, **data_dict)

        assert 'User not authenticated' in str(exc_info.value)

    def test_metabase_user_created_cards_list_no_email_found(self, mock_metabase_config):
        """Test listing cards when user has no email"""
        user = factories.User()
        # Create a mock user object without email or name
        # The action checks: getattr(userobj, 'email', None) or userobj.name
        # So both need to be falsy to trigger the ValidationError
        mock_user_obj = mock.Mock()
        mock_user_obj.email = None
        mock_user_obj.name = None

        context = {
            'user': user['name'],
            'auth_user_obj': mock_user_obj
        }
        data_dict = {}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_user_created_cards_list', context, **data_dict)

        assert 'User email not found' in str(exc_info.value)


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestMetabaseUserCreatedDashboardsList:
    """Test metabase user created dashboards listing actions"""

    def test_metabase_user_created_dashboards_list_with_email(self, mock_metabase_config):
        """Test listing dashboards with email parameter"""
        user = factories.User(email='test@example.com')
        expected_dashboards = [
            {
                'id': 1,
                'name': 'Test Dashboard 1',
                'description': 'Description 1',
                'created_at': None,
                'updated_at': None,
                'creator_id': 123
            },
            {
                'id': 2,
                'name': 'Test Dashboard 2',
                'description': 'Description 2',
                'created_at': None,
                'updated_at': None,
                'creator_id': 123
            }
        ]

        context = {'user': user['name']}
        data_dict = {'email': 'test@example.com'}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.utils.get_metabase_user_created_dashboards', return_value=expected_dashboards):
            result = call_action('metabase_user_created_dashboards_list', context, **data_dict)

        assert result == expected_dashboards
        assert len(result) == 2

    def test_metabase_user_created_dashboards_list_without_email(self, mock_metabase_config):
        """Test listing dashboards using current user's email"""
        user = factories.User(email='test@example.com')
        expected_dashboards = [
            {
                'id': 1,
                'name': 'Test Dashboard',
                'description': 'Description',
                'created_at': None,
                'updated_at': None,
                'creator_id': 123
            }
        ]

        # Create a mock user object
        mock_user_obj = mock.Mock()
        mock_user_obj.email = user.get('email')
        mock_user_obj.name = user['name']

        context = {
            'user': user['name'],
            'auth_user_obj': mock_user_obj
        }
        data_dict = {}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.utils.get_metabase_user_created_dashboards', return_value=expected_dashboards):
            result = call_action('metabase_user_created_dashboards_list', context, **data_dict)

        assert result == expected_dashboards

    def test_metabase_user_created_dashboards_list_no_dashboards(self, mock_metabase_config):
        """Test listing dashboards when no dashboards found"""
        user = factories.User(email='test@example.com')

        context = {'user': user['name']}
        data_dict = {'email': 'test@example.com'}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.utils.get_metabase_user_created_dashboards', return_value=[]):
            result = call_action('metabase_user_created_dashboards_list', context, **data_dict)

        assert result == []

    def test_metabase_user_created_dashboards_list_not_authenticated(self, mock_metabase_config):
        """Test listing dashboards when user is not authenticated"""
        # Set auth_user_obj to None explicitly in context
        context = {'auth_user_obj': None}
        data_dict = {}

        # Mock tk.g.userobj to return None without requiring app context
        mock_g = mock.MagicMock()
        mock_g.userobj = None

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             mock.patch('ckanext.in_app_reporting.action.tk.g', mock_g):
            with pytest.raises(toolkit.NotAuthorized) as exc_info:
                call_action('metabase_user_created_dashboards_list', context, **data_dict)

        assert 'User not authenticated' in str(exc_info.value)

    def test_metabase_user_created_dashboards_list_no_email_found(self, mock_metabase_config):
        """Test listing dashboards when user has no email"""
        user = factories.User()
        # Create a mock user object without email or name
        # The action checks: getattr(userobj, 'email', None) or userobj.name
        # So both need to be falsy to trigger the ValidationError
        mock_user_obj = mock.Mock()
        mock_user_obj.email = None
        mock_user_obj.name = None

        context = {
            'user': user['name'],
            'auth_user_obj': mock_user_obj
        }
        data_dict = {}

        with mock.patch('ckan.plugins.toolkit.check_access'), \
             pytest.raises(toolkit.ValidationError) as exc_info:
            call_action('metabase_user_created_dashboards_list', context, **data_dict)

        assert 'User email not found' in str(exc_info.value) 