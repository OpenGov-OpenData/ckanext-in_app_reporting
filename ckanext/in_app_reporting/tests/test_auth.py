"""
Tests for auth.py authorization functions.
"""
import pytest
from unittest import mock
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories

import ckanext.in_app_reporting.auth as auth


class TestMetabaseMappingAuth:
    """Test authorization for metabase mapping functions"""

    def test_metabase_mapping_create_always_denies(self):
        """Test that metabase_mapping_create always returns False"""
        context = {'user': 'test-user'}
        data_dict = {}

        result = auth.metabase_mapping_create(context, data_dict)

        assert result['success'] is False

    def test_metabase_mapping_update_always_denies(self):
        """Test that metabase_mapping_update always returns False"""
        context = {'user': 'test-user'}
        data_dict = {}

        result = auth.metabase_mapping_update(context, data_dict)

        assert result['success'] is False

    def test_metabase_mapping_delete_always_denies(self):
        """Test that metabase_mapping_delete always returns False"""
        context = {'user': 'test-user'}
        data_dict = {}

        result = auth.metabase_mapping_delete(context, data_dict)

        assert result['success'] is False

    def test_metabase_mapping_show_always_denies(self):
        """Test that metabase_mapping_show always returns False"""
        context = {'user': 'test-user'}
        data_dict = {}

        result = auth.metabase_mapping_show(context, data_dict)

        assert result['success'] is False

    def test_metabase_mapping_list_always_denies(self):
        """Test that metabase_mapping_list always returns False"""
        context = {'user': 'test-user'}
        data_dict = {}

        result = auth.metabase_mapping_list(context, data_dict)

        assert result['success'] is False


class TestMetabaseEmbedAuth:
    """Test authorization for metabase embed function"""

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    def test_metabase_embed_with_sso_user(self, mock_is_sso_user):
        """Test metabase_embed authorization with SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = True

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_embed(context, data_dict)

        assert result['success'] is True
        mock_is_sso_user.assert_called_once()

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    def test_metabase_embed_with_non_sso_user(self, mock_is_sso_user):
        """Test metabase_embed authorization with non-SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = False

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_embed(context, data_dict)

        assert result['success'] is False
        mock_is_sso_user.assert_called_once()

    def test_metabase_embed_with_no_user(self):
        """Test metabase_embed authorization with no user"""
        context = {'user': None}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=None):
            result = auth.metabase_embed(context, data_dict)

        assert result['success'] is False


class TestMetabaseSsoAuth:
    """Test authorization for metabase SSO function"""

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    def test_metabase_sso_with_sso_user(self, mock_is_sso_user):
        """Test metabase_sso authorization with SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = True

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_sso(context, data_dict)

        assert result['success'] is True
        mock_is_sso_user.assert_called_once()

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    def test_metabase_sso_with_non_sso_user(self, mock_is_sso_user):
        """Test metabase_sso authorization with non-SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = False

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_sso(context, data_dict)

        assert result['success'] is False


class TestMetabaseDataAuth:
    """Test authorization for metabase data function"""

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_data_with_authorized_sso_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_data authorization with authorized SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = True
        mock_check_access.return_value = None  # No exception means authorized

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_data(context, data_dict)

        assert result['success'] is True
        mock_is_sso_user.assert_called_once()
        mock_check_access.assert_called_once_with('resource_update', context, data_dict)

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_data_with_unauthorized_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_data authorization with unauthorized user"""
        user = factories.User()
        mock_is_sso_user.return_value = True
        mock_check_access.side_effect = toolkit.NotAuthorized('Not authorized')

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_data(context, data_dict)

        assert result['success'] is False
        assert 'User {0} not authorized'.format(user['name']) in result['msg']

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_data_with_authorized_non_sso_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_data authorization with authorized but non-SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = False
        mock_check_access.return_value = None

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_data(context, data_dict)

        assert result['success'] is False


class TestMetabaseCardPublishAuth:
    """Test authorization for metabase card publish function"""

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_card_publish_with_authorized_sso_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_card_publish authorization with authorized SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = True
        mock_check_access.return_value = None

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_card_publish(context, data_dict)

        assert result['success'] is True
        mock_is_sso_user.assert_called_once()
        mock_check_access.assert_called_once_with('resource_update', context, data_dict)

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_card_publish_with_unauthorized_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_card_publish authorization with unauthorized user"""
        user = factories.User()
        mock_is_sso_user.return_value = True
        mock_check_access.side_effect = toolkit.NotAuthorized('Not authorized')

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_card_publish(context, data_dict)

        assert result['success'] is False
        assert 'User {0} not authorized'.format(user['name']) in result['msg']

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_card_publish_with_authorized_non_sso_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_card_publish authorization with authorized but non-SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = False
        mock_check_access.return_value = None

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_card_publish(context, data_dict)

        assert result['success'] is False


class TestMetabaseDashboardPublishAuth:
    """Test authorization for metabase dashboard publish function"""

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_dashboard_publish_with_authorized_sso_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_dashboard_publish authorization with authorized SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = True
        mock_check_access.return_value = None

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_dashboard_publish(context, data_dict)

        assert result['success'] is True
        mock_is_sso_user.assert_called_once()
        mock_check_access.assert_called_once_with('resource_update', context, data_dict)

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_dashboard_publish_with_unauthorized_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_dashboard_publish authorization with unauthorized user"""
        user = factories.User()
        mock_is_sso_user.return_value = True
        mock_check_access.side_effect = toolkit.NotAuthorized('Not authorized')

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_dashboard_publish(context, data_dict)

        assert result['success'] is False
        assert 'User {0} not authorized'.format(user['name']) in result['msg']

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_dashboard_publish_with_authorized_non_sso_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_dashboard_publish authorization with authorized but non-SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = False
        mock_check_access.return_value = None

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_dashboard_publish(context, data_dict)

        assert result['success'] is False


class TestMetabaseModelCreateAuth:
    """Test authorization for metabase model create function"""

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_model_create_with_authorized_sso_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_model_create authorization with authorized SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = True
        mock_check_access.return_value = None

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_model_create(context, data_dict)

        assert result['success'] is True
        mock_is_sso_user.assert_called_once()
        mock_check_access.assert_called_once_with('resource_update', context, data_dict)

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_model_create_with_unauthorized_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_model_create authorization with unauthorized user"""
        user = factories.User()
        mock_is_sso_user.return_value = True
        mock_check_access.side_effect = toolkit.NotAuthorized('Not authorized')

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_model_create(context, data_dict)

        assert result['success'] is False
        assert 'User {0} not authorized to create Metabase model'.format(user['name']) in result['msg']

    @mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user')
    @mock.patch('ckan.plugins.toolkit.check_access')
    def test_metabase_model_create_with_authorized_non_sso_user(self, mock_check_access, mock_is_sso_user):
        """Test metabase_model_create authorization with authorized but non-SSO user"""
        user = factories.User()
        mock_is_sso_user.return_value = False
        mock_check_access.return_value = None

        context = {'user': user['name']}
        data_dict = {}

        with mock.patch('ckan.model.User.get', return_value=user):
            result = auth.metabase_model_create(context, data_dict)

        assert result['success'] is False


class TestAuthIntegration:
    """Integration tests for auth functions"""

    def test_all_auth_functions_return_dict_with_success_key(self):
        """Test that all auth functions return a dict with 'success' key"""
        context = {'user': 'test-user'}
        data_dict = {}

        auth_functions = [
            auth.metabase_mapping_create,
            auth.metabase_mapping_update,
            auth.metabase_mapping_delete,
            auth.metabase_mapping_show,
            auth.metabase_mapping_list,
            auth.metabase_embed,
            auth.metabase_sso,
            auth.metabase_data,
            auth.metabase_card_publish,
            auth.metabase_dashboard_publish,
            auth.metabase_model_create
        ]

        with mock.patch('ckan.model.User.get', return_value=None), \
             mock.patch('ckanext.in_app_reporting.utils.is_metabase_sso_user', return_value=False), \
             mock.patch('ckan.plugins.toolkit.check_access', side_effect=toolkit.NotAuthorized()):
    
            for auth_func in auth_functions:
                result = auth_func(context, data_dict)
                assert isinstance(result, dict)
                assert 'success' in result
                assert isinstance(result['success'], bool) 