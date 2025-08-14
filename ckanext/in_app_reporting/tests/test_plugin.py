"""
Tests for plugin.py.

Tests are written using the pytest library (https://docs.pytest.org), and you
should read the testing guidelines in the CKAN docs:
https://docs.ckan.org/en/2.9/contributing/testing.html
"""
import pytest
from unittest import mock
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories

from ckanext.in_app_reporting.plugin import (
    InAppReportingPlugin,
    MetabaseCardViewPlugin,
    MetabaseDashboardViewPlugin,
    configurable_defaults_validator
)


class TestInAppReportingPlugin:
    """Test the main InAppReportingPlugin class"""

    def test_update_config(self):
        """Test that update_config adds template directories and resources"""
        plugin = InAppReportingPlugin()
        config = {}

        with mock.patch('ckan.plugins.toolkit.add_template_directory') as mock_add_template, \
             mock.patch('ckan.plugins.toolkit.add_public_directory') as mock_add_public, \
             mock.patch('ckan.plugins.toolkit.add_resource') as mock_add_resource:

            plugin.update_config(config)

            mock_add_template.assert_called_once_with(config, 'templates')
            mock_add_public.assert_called_once_with(config, 'public')
            mock_add_resource.assert_called_once_with('assets', 'reporting')

    def test_get_actions(self):
        """Test that get_actions returns correct action functions"""
        plugin = InAppReportingPlugin()
        actions = plugin.get_actions()

        expected_actions = [
            'metabase_mapping_create',
            'metabase_mapping_update',
            'metabase_mapping_delete',
            'metabase_mapping_show',
            'metabase_mapping_list',
            'metabase_card_publish',
            'metabase_dashboard_publish',
            'metabase_model_create',
            'metabase_sql_questions_list'
        ]

        for action_name in expected_actions:
            assert action_name in actions
            assert callable(actions[action_name])

    def test_get_auth_functions(self):
        """Test that get_auth_functions returns correct auth functions"""
        plugin = InAppReportingPlugin()
        auth_functions = plugin.get_auth_functions()

        expected_auth_functions = [
            'metabase_mapping_create',
            'metabase_mapping_update',
            'metabase_mapping_delete',
            'metabase_mapping_show',
            'metabase_mapping_list',
            'metabase_embed',
            'metabase_sso',
            'metabase_data',
            'metabase_card_publish',
            'metabase_dashboard_publish',
            'metabase_model_create'
        ]

        for auth_name in expected_auth_functions:
            assert auth_name in auth_functions
            assert callable(auth_functions[auth_name])

    def test_get_helpers(self):
        """Test that get_helpers returns template helper functions"""
        plugin = InAppReportingPlugin()
        helpers = plugin.get_helpers()

        expected_helpers = [
            'is_metabase_sso_user',
            'get_metabase_embeddable',
            'get_metabase_collection_id',
            'get_metabase_table_id',
            'get_metabase_model_id',
            'get_metabase_cards_by_table_id'
        ]

        for helper_name in expected_helpers:
            assert helper_name in helpers
            assert callable(helpers[helper_name])


class TestMetabaseCardViewPlugin:
    """Test the MetabaseCardViewPlugin class"""

    def test_info(self):
        """Test that info returns correct view metadata"""
        plugin = MetabaseCardViewPlugin()
        info = plugin.info()

        assert info['name'] == 'metabase_card_view'
        assert info['title'] == 'Insights (Chart)'
        assert info['default_title'] == 'Chart'
        assert info['icon'] == 'bar-chart'
        assert info['always_available'] is False
        assert info['iframed'] is True
        assert info['preview_enabled'] is True
        assert 'schema' in info
        assert 'entity_id' in info['schema']

    def test_view_template(self):
        """Test view_template returns correct template"""
        plugin = MetabaseCardViewPlugin()
        template = plugin.view_template({}, {})

        assert template == 'metabase/card_view.html'

    def test_form_template(self):
        """Test form_template returns correct template"""
        plugin = MetabaseCardViewPlugin()
        template = plugin.form_template({}, {})

        assert template == 'metabase/card_form.html'

    def test_get_helpers_card_view(self):
        """Test get_helpers returns iframe URL helper"""
        plugin = MetabaseCardViewPlugin()
        helpers = plugin.get_helpers()

        assert 'get_metabase_iframe_url' in helpers
        assert callable(helpers['get_metabase_iframe_url'])


class TestMetabaseDashboardViewPlugin:
    """Test the MetabaseDashboardViewPlugin class"""

    def test_info(self):
        """Test that info returns correct view metadata"""
        plugin = MetabaseDashboardViewPlugin()
        info = plugin.info()

        assert info['name'] == 'metabase_dashboard_view'
        assert info['title'] == 'Insights (Dashboard)'
        assert info['default_title'] == 'Dashboard'
        assert info['icon'] == 'bar-chart'
        assert info['always_available'] is False
        assert info['iframed'] is True
        assert info['preview_enabled'] is True
        assert 'schema' in info
        assert 'entity_id' in info['schema']
        assert 'downloads' in info['schema']

    def test_view_template(self):
        """Test view_template returns correct template"""
        plugin = MetabaseDashboardViewPlugin()
        template = plugin.view_template({}, {})

        assert template == 'metabase/dashboard_view.html'

    def test_form_template(self):
        """Test form_template returns correct template"""
        plugin = MetabaseDashboardViewPlugin()
        template = plugin.form_template({}, {})

        assert template == 'metabase/dashboard_form.html'


class TestConfigurableDefaultsValidator:
    """Test the configurable_defaults_validator function"""

    def test_validator_for_view_context_with_missing_value(self):
        """Test validator sets False when for_view context and value is missing"""
        validator = configurable_defaults_validator(True)

        key = 'test_key'
        data = {key: toolkit.missing}
        errors = {}
        context = {'for_view': True}

        validator(key, data, errors, context)

        assert data[key] is False

    def test_validator_for_view_context_with_none_value(self):
        """Test validator sets False when for_view context and value is None"""
        validator = configurable_defaults_validator(True)

        key = 'test_key'
        data = {key: None}
        errors = {}
        context = {'for_view': True}

        validator(key, data, errors, context)

        assert data[key] is False

    def test_validator_for_view_context_with_empty_string(self):
        """Test validator sets False when for_view context and value is empty string"""
        validator = configurable_defaults_validator(True)

        key = 'test_key'
        data = {key: ''}
        errors = {}
        context = {'for_view': True}

        validator(key, data, errors, context)

        assert data[key] is False

    def test_validator_for_non_view_context(self):
        """Test validator sets default value when not for_view context"""
        default_value = True
        validator = configurable_defaults_validator(default_value)

        key = 'test_key'
        data = {key: None}
        errors = {}
        context = {}

        validator(key, data, errors, context)

        assert data[key] == default_value

    def test_validator_preserves_existing_valid_value(self):
        """Test validator preserves existing valid value in for_view context"""
        validator = configurable_defaults_validator(True)

        key = 'test_key'
        data = {key: 'valid_value'}
        errors = {}
        context = {'for_view': True}

        validator(key, data, errors, context)

        assert data[key] == 'valid_value'


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestPluginIntegration:
    """Integration tests for the plugin"""

    def test_actions_are_available(self):
        """Test that all actions are available after plugin load"""
        expected_actions = [
            'metabase_mapping_create',
            'metabase_mapping_update',
            'metabase_mapping_delete',
            'metabase_mapping_show',
            'metabase_mapping_list',
            'metabase_card_publish',
            'metabase_dashboard_publish',
            'metabase_model_create',
            'metabase_sql_questions_list'
        ]

        for action_name in expected_actions:
            assert toolkit.get_action(action_name) is not None

    def test_helpers_are_available(self):
        """Test that template helpers are available after plugin load"""
        expected_helpers = [
            'is_metabase_sso_user',
            'get_metabase_embeddable',
            'get_metabase_collection_id',
            'get_metabase_table_id',
            'get_metabase_model_id',
            'get_metabase_cards_by_table_id'
        ]

        for helper_name in expected_helpers:
            assert toolkit.h.get(helper_name) is not None
