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
