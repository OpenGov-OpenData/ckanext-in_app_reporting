import pytest

from ckantoolkit import url_for
from ckantoolkit.tests import factories
import ckan.plugins.toolkit as toolkit

# We rely on fixtures defined in this extension's tests/fixtures.py:
# - mock_is_metabase_sso_user: force SSO checks to pass where required


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestBlueprint:

    def test_insights_page_is_rendered(self, app, mock_is_metabase_sso_user):
        url = url_for('metabase.metabase_embed')
        sysadmin = factories.Sysadmin()
        env = {"REMOTE_USER": sysadmin['name'].encode('ascii')}

        response = app.get(url, extra_environ=env)

        assert 'id="metabase-interactive-embed"' in response.body

    def test_metabase_data_page_rendered(self, app, mock_is_metabase_sso_user):
        dataset = factories.Dataset(title='Test Dataset')
        resource = factories.Resource(package_id=dataset['id'], name='Test Resource')

        url = url_for('metabase.metabase_data', id=dataset['id'], resource_id=resource['id'])
        sysadmin = factories.Sysadmin()
        env = {"REMOTE_USER": sysadmin['name'].encode('ascii')}

        response = app.get(url, extra_environ=env)

        assert 'Datastore Table ID:' in response.body
        assert resource['id'] in response.body

    def test_create_chart_redirects_to_existing_model(self, app, mock_is_metabase_sso_user, mock_check_access, monkeypatch):
        dataset = factories.Dataset(title='Test Dataset')
        resource = factories.Resource(package_id=dataset['id'], name='Test Resource')

        # Simulate an existing Metabase model for the resource
        monkeypatch.setattr('ckanext.in_app_reporting.utils.get_metabase_table_id', lambda rid: 123)
        monkeypatch.setattr('ckanext.in_app_reporting.utils.get_metabase_model_id', lambda table_id: 456)

        url = url_for('metabase.create_chart', id=dataset['id'], resource_id=resource['id'])
        sysadmin = factories.Sysadmin()
        env = {"REMOTE_USER": sysadmin['name'].encode('ascii')}

        response = app.get(url, extra_environ=env)

        assert 'id="metabase-interactive-embed"' in response.body
        assert 'return_to=/model/456' in response.body

    def test_create_chart_creates_model_and_redirects(self, app, mock_is_metabase_sso_user, mock_check_access, monkeypatch):
        dataset = factories.Dataset(title='Test Dataset')
        resource = factories.Resource(package_id=dataset['id'], name='Test Resource')

        # Ensure no existing model is found
        monkeypatch.setattr('ckanext.in_app_reporting.utils.get_metabase_table_id', lambda rid: None)

        # Intercept only metabase_model_create; delegate all other actions
        original_get_action = toolkit.get_action

        def fake_get_action(name):
            if name == 'metabase_model_create':
                def create_model(context, data_dict):
                    return {'id': 789, 'success': True}
                return create_model
            return original_get_action(name)

        monkeypatch.setattr('ckanext.in_app_reporting.blueprint.tk.get_action', fake_get_action)

        url = url_for('metabase.create_chart', id=dataset['id'], resource_id=resource['id'])
        sysadmin = factories.Sysadmin()
        env = {"REMOTE_USER": sysadmin['name'].encode('ascii')}

        response = app.get(url, extra_environ=env)

        assert 'id="metabase-interactive-embed"' in response.body
        assert 'return_to=/model/789' in response.body

    def test_create_chart_fallback_redirect_on_creation_error(self, app, mock_is_metabase_sso_user, mock_check_access, monkeypatch):
        dataset = factories.Dataset(title='Test Dataset')
        resource = factories.Resource(package_id=dataset['id'], name='Test Resource')

        # Ensure no existing model is found
        monkeypatch.setattr('ckanext.in_app_reporting.utils.get_metabase_table_id', lambda rid: None)

        # Intercept only metabase_model_create to raise a validation error
        original_get_action = toolkit.get_action

        def fake_get_action(name):
            if name == 'metabase_model_create':
                def create_model(context, data_dict):
                    raise toolkit.ValidationError('boom')
                return create_model
            return original_get_action(name)

        monkeypatch.setattr('ckanext.in_app_reporting.blueprint.tk.get_action', fake_get_action)

        url = url_for('metabase.create_chart', id=dataset['id'], resource_id=resource['id'])
        sysadmin = factories.Sysadmin()
        env = {"REMOTE_USER": sysadmin['name'].encode('ascii')}

        response = app.get(url, extra_environ=env)

        # Default collection id comes from test.ini -> first is '1'
        assert 'id="metabase-interactive-embed"' in response.body
        assert 'return_to=/collection/1' in response.body

    def test_collection_items_list_returns_results(self, app, mock_is_metabase_sso_user, monkeypatch):
        # Stub utils to avoid external calls
        monkeypatch.setattr(
            'ckanext.in_app_reporting.utils.get_metabase_collection_items',
            lambda model_type: [
                {'id': 1, 'name': 'Card 1', 'type': 'card'},
                {'id': 2, 'name': 'Card 2', 'type': 'card'},
            ]
        )

        url = url_for('metabase.get_metabase_collection_items', model_type='card')
        sysadmin = factories.Sysadmin()
        env = {"REMOTE_USER": sysadmin['name'].encode('ascii')}

        response = app.get(url, extra_environ=env)

        assert response.json == {
            'results': [
                {'id': 1, 'name': 'Card 1', 'type': 'card'},
                {'id': 2, 'name': 'Card 2', 'type': 'card'},
            ]
        }

    def test_collection_items_list_question_type_maps_to_card(self, app, mock_is_metabase_sso_user, monkeypatch):
        captured = {'model_type': None}

        def fake_get_items(model_type):
            captured['model_type'] = model_type
            return []

        monkeypatch.setattr(
            'ckanext.in_app_reporting.utils.get_metabase_collection_items',
            fake_get_items
        )

        url = url_for('metabase.get_metabase_collection_items', model_type='question')
        sysadmin = factories.Sysadmin()
        env = {"REMOTE_USER": sysadmin['name'].encode('ascii')}

        app.get(url, extra_environ=env)

        # Blueprint should convert 'question' to 'card'
        assert captured['model_type'] == 'card'

    def test_user_created_cards_page_rendered(self, app, mock_is_metabase_sso_user, mock_check_access, monkeypatch):
        """Test user created cards page is rendered"""
        user = factories.Sysadmin()
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
            }
        ]

        def fake_get_action(name):
            if name == 'metabase_user_created_cards_list':
                def cards_list(context, data_dict):
                    return expected_cards
                return cards_list
            if name == 'user_show':
                def user_show(context, data_dict):
                    return {'id': user['id'], 'name': user['name'], 'email': user.get('email')}
                return user_show
            return toolkit.get_action(name)

        monkeypatch.setattr('ckanext.in_app_reporting.blueprint.tk.get_action', fake_get_action)

        url = url_for('metabase.user_created_cards_page')
        env = {"REMOTE_USER": user['name'].encode('ascii')}

        response = app.get(url, extra_environ=env)

        assert response.status_code == 200
        assert 'Recent Insights Charts' in response.body
        assert 'Test Card 1' in response.body

    def test_user_created_cards_page_no_cards(self, app, mock_is_metabase_sso_user, mock_check_access, monkeypatch):
        """Test user created cards page when no cards found"""
        user = factories.Sysadmin()

        def fake_get_action(name):
            if name == 'metabase_user_created_cards_list':
                def cards_list(context, data_dict):
                    return []
                return cards_list
            if name == 'user_show':
                def user_show(context, data_dict):
                    return {'id': user['id'], 'name': user['name'], 'email': user.get('email')}
                return user_show
            return toolkit.get_action(name)

        monkeypatch.setattr('ckanext.in_app_reporting.blueprint.tk.get_action', fake_get_action)

        url = url_for('metabase.user_created_cards_page')
        env = {"REMOTE_USER": user['name'].encode('ascii')}

        response = app.get(url, extra_environ=env)

        assert response.status_code == 200
        assert 'You have not created any charts yet' in response.body

    def test_user_created_cards_page_not_sso_user(self, app, mock_check_access, monkeypatch):
        """Test user created cards page when user is not SSO user"""
        user = factories.Sysadmin()

        monkeypatch.setattr('ckanext.in_app_reporting.utils.is_metabase_sso_user', lambda u: False)

        url = url_for('metabase.user_created_cards_page')
        env = {"REMOTE_USER": user['name'].encode('ascii')}

        response = app.get(url, extra_environ=env, expect_errors=True)

        assert response.status_code == 404

    def test_user_created_dashboards_page_rendered(self, app, mock_is_metabase_sso_user, mock_check_access, monkeypatch):
        """Test user created dashboards page is rendered"""
        user = factories.Sysadmin()
        expected_dashboards = [
            {
                'id': 1,
                'name': 'Test Dashboard 1',
                'description': 'Description 1',
                'created_at': None,
                'updated_at': None,
                'creator_id': 123
            }
        ]

        def fake_get_action(name):
            if name == 'metabase_user_created_dashboards_list':
                def dashboards_list(context, data_dict):
                    return expected_dashboards
                return dashboards_list
            if name == 'user_show':
                def user_show(context, data_dict):
                    return {'id': user['id'], 'name': user['name'], 'email': user.get('email')}
                return user_show
            return toolkit.get_action(name)

        monkeypatch.setattr('ckanext.in_app_reporting.blueprint.tk.get_action', fake_get_action)

        url = url_for('metabase.user_created_dashboards_page')
        env = {"REMOTE_USER": user['name'].encode('ascii')}

        response = app.get(url, extra_environ=env)

        assert response.status_code == 200
        assert 'Recent Insights Dashboards' in response.body
        assert 'Test Dashboard 1' in response.body

    def test_user_created_dashboards_page_no_dashboards(self, app, mock_is_metabase_sso_user, mock_check_access, monkeypatch):
        """Test user created dashboards page when no dashboards found"""
        user = factories.Sysadmin()

        def fake_get_action(name):
            if name == 'metabase_user_created_dashboards_list':
                def dashboards_list(context, data_dict):
                    return []
                return dashboards_list
            if name == 'user_show':
                def user_show(context, data_dict):
                    return {'id': user['id'], 'name': user['name'], 'email': user.get('email')}
                return user_show
            return toolkit.get_action(name)

        monkeypatch.setattr('ckanext.in_app_reporting.blueprint.tk.get_action', fake_get_action)

        url = url_for('metabase.user_created_dashboards_page')
        env = {"REMOTE_USER": user['name'].encode('ascii')}

        response = app.get(url, extra_environ=env)

        assert response.status_code == 200
        assert 'You have not created any dashboards yet' in response.body

    def test_user_created_dashboards_page_not_sso_user(self, app, mock_check_access, monkeypatch):
        """Test user created dashboards page when user is not SSO user"""
        user = factories.Sysadmin()

        monkeypatch.setattr('ckanext.in_app_reporting.utils.is_metabase_sso_user', lambda u: False)

        url = url_for('metabase.user_created_dashboards_page')
        env = {"REMOTE_USER": user['name'].encode('ascii')}

        response = app.get(url, extra_environ=env, expect_errors=True)

        assert response.status_code == 404
