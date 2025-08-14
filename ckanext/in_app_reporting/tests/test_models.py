"""
Tests for model.py database models.
"""
import pytest
import datetime
from unittest import mock
import ckan.model as model
from ckan.tests import factories

from ckanext.in_app_reporting.model import MetabaseMapping, table_dictize


class TestMetabaseMappingModel:
    """Test the MetabaseMapping model"""

    @pytest.mark.usefixtures('with_plugins', 'clean_db')
    @pytest.mark.ckan_config('ckan.plugins', 'in_app_reporting')
    def test_metabase_mapping_creation(self):
        """Test creating a MetabaseMapping instance"""
        user = factories.User()

        mapping = MetabaseMapping(
            user_id=user['id'],
            platform_uuid='12345678-1234-1234-1234-123456789012',
            email=user['email'],
            group_ids='group1;group2',
            collection_ids='col1;col2'
        )

        model.Session.add(mapping)
        model.Session.commit()

        assert mapping.user_id == user['id']
        assert mapping.platform_uuid == '12345678-1234-1234-1234-123456789012'
        assert mapping.email == user['email']
        assert mapping.group_ids == 'group1;group2'
        assert mapping.collection_ids == 'col1;col2'
        assert isinstance(mapping.created, datetime.datetime)
        assert isinstance(mapping.modified, datetime.datetime)

    @pytest.mark.usefixtures('with_plugins', 'clean_db')
    @pytest.mark.ckan_config('ckan.plugins', 'in_app_reporting')
    def test_metabase_mapping_get_by_user_id(self):
        """Test getting MetabaseMapping by user_id"""
        user = factories.User()

        mapping = MetabaseMapping(
            user_id=user['id'],
            platform_uuid='12345678-1234-1234-1234-123456789012',
            email=user['email'],
            group_ids='group1;group2',
            collection_ids='col1;col2'
        )

        model.Session.add(mapping)
        model.Session.commit()

        retrieved_mapping = MetabaseMapping.get(user_id=user['id'])

        assert retrieved_mapping is not None
        assert retrieved_mapping.user_id == user['id']
        assert retrieved_mapping.platform_uuid == '12345678-1234-1234-1234-123456789012'
        assert retrieved_mapping.email == user['email']

    @pytest.mark.usefixtures('with_plugins', 'clean_db')
    @pytest.mark.ckan_config('ckan.plugins', 'in_app_reporting')
    def test_metabase_mapping_get_by_email(self):
        """Test getting MetabaseMapping by email"""
        user = factories.User()

        mapping = MetabaseMapping(
            user_id=user['id'],
            platform_uuid='12345678-1234-1234-1234-123456789012',
            email=user['email'],
            group_ids='group1;group2',
            collection_ids='col1;col2'
        )

        model.Session.add(mapping)
        model.Session.commit()

        retrieved_mapping = MetabaseMapping.get(email=user['email'])

        assert retrieved_mapping is not None
        assert retrieved_mapping.user_id == user['id']
        assert retrieved_mapping.email == user['email']

    @pytest.mark.usefixtures('with_plugins', 'clean_db')
    @pytest.mark.ckan_config('ckan.plugins', 'in_app_reporting')
    def test_metabase_mapping_get_nonexistent(self):
        """Test getting non-existent MetabaseMapping"""
        retrieved_mapping = MetabaseMapping.get(user_id='nonexistent-user-id')

        assert retrieved_mapping is None

    @pytest.mark.usefixtures('with_plugins', 'clean_db')
    @pytest.mark.ckan_config('ckan.plugins', 'in_app_reporting')
    def test_metabase_mapping_multiple_conditions(self):
        """Test getting MetabaseMapping with multiple conditions"""
        user = factories.User()

        mapping = MetabaseMapping(
            user_id=user['id'],
            platform_uuid='12345678-1234-1234-1234-123456789012',
            email=user['email'],
            group_ids='group1;group2',
            collection_ids='col1;col2'
        )

        model.Session.add(mapping)
        model.Session.commit()

        retrieved_mapping = MetabaseMapping.get(user_id=user['id'], email=user['email'])

        assert retrieved_mapping is not None
        assert retrieved_mapping.user_id == user['id']
        assert retrieved_mapping.email == user['email']

    @pytest.mark.usefixtures('with_plugins', 'clean_db')
    @pytest.mark.ckan_config('ckan.plugins', 'in_app_reporting')
    def test_metabase_mapping_default_timestamps(self):
        """Test that MetabaseMapping has default timestamps"""
        user = factories.User()

        # Create mapping without explicit timestamps
        mapping = MetabaseMapping(
            user_id=user['id'],
            platform_uuid='12345678-1234-1234-1234-123456789012',
            email=user['email'],
            group_ids='group1',
            collection_ids='col1'
        )

        model.Session.add(mapping)
        model.Session.commit()

        # Refresh the object to get database defaults
        model.Session.refresh(mapping)

        assert mapping.created is not None
        assert mapping.modified is not None
        assert isinstance(mapping.created, datetime.datetime)
        assert isinstance(mapping.modified, datetime.datetime)

    @pytest.mark.usefixtures('with_plugins', 'clean_db')
    @pytest.mark.ckan_config('ckan.plugins', 'in_app_reporting')
    def test_metabase_mapping_update(self):
        """Test updating a MetabaseMapping"""
        user = factories.User()

        mapping = MetabaseMapping(
            user_id=user['id'],
            platform_uuid='12345678-1234-1234-1234-123456789012',
            email=user['email'],
            group_ids='group1',
            collection_ids='col1'
        )

        model.Session.add(mapping)
        model.Session.commit()

        # Update the mapping
        mapping.group_ids = 'group1;group2;group3'
        mapping.collection_ids = 'col1;col2'
        mapping.modified = datetime.datetime.utcnow()

        model.Session.commit()

        # Retrieve and verify the update
        updated_mapping = MetabaseMapping.get(user_id=user['id'])

        assert updated_mapping.group_ids == 'group1;group2;group3'
        assert updated_mapping.collection_ids == 'col1;col2'

    @pytest.mark.usefixtures('with_plugins', 'clean_db')
    @pytest.mark.ckan_config('ckan.plugins', 'in_app_reporting')
    def test_metabase_mapping_delete(self):
        """Test deleting a MetabaseMapping"""
        user = factories.User()

        mapping = MetabaseMapping(
            user_id=user['id'],
            platform_uuid='12345678-1234-1234-1234-123456789012',
            email=user['email'],
            group_ids='group1',
            collection_ids='col1'
        )

        model.Session.add(mapping)
        model.Session.commit()

        # Verify it exists
        assert MetabaseMapping.get(user_id=user['id']) is not None

        # Delete it
        model.Session.delete(mapping)
        model.Session.commit()

        # Verify it's gone
        assert MetabaseMapping.get(user_id=user['id']) is None

    @pytest.mark.usefixtures('with_plugins', 'clean_db')
    @pytest.mark.ckan_config('ckan.plugins', 'in_app_reporting')
    def test_metabase_mapping_cascade_delete(self):
        """Test that MetabaseMapping is deleted when user is deleted"""
        user = factories.User()

        mapping = MetabaseMapping(
            user_id=user['id'],
            platform_uuid='12345678-1234-1234-1234-123456789012',
            email=user['email'],
            group_ids='group1',
            collection_ids='col1'
        )

        model.Session.add(mapping)
        model.Session.commit()

        # Verify mapping exists
        assert MetabaseMapping.get(user_id=user['id']) is not None

        # Delete the user
        user_obj = model.User.get(user['id'])
        if user_obj:
            model.Session.delete(user_obj)
            model.Session.commit()

        # Verify mapping is also deleted due to CASCADE
        assert MetabaseMapping.get(user_id=user['id']) is None

    @pytest.mark.usefixtures('with_plugins', 'clean_db')
    @pytest.mark.ckan_config('ckan.plugins', 'in_app_reporting')
    def test_metabase_mapping_nullable_fields(self):
        """Test MetabaseMapping with nullable fields"""
        user = factories.User()

        # Create mapping with minimal required fields
        mapping = MetabaseMapping(
            user_id=user['id'],
            platform_uuid='12345678-1234-1234-1234-123456789012',
            email=user['email']
            # group_ids and collection_ids are nullable
        )

        model.Session.add(mapping)
        model.Session.commit()

        retrieved_mapping = MetabaseMapping.get(user_id=user['id'])

        assert retrieved_mapping is not None
        assert retrieved_mapping.user_id == user['id']
        assert retrieved_mapping.platform_uuid == '12345678-1234-1234-1234-123456789012'
        assert retrieved_mapping.email == user['email']
        assert retrieved_mapping.group_ids is None
        assert retrieved_mapping.collection_ids is None


class TestTableDictize:
    """Test the table_dictize utility function"""

    @pytest.mark.usefixtures('with_plugins', 'clean_db')
    @pytest.mark.ckan_config('ckan.plugins', 'in_app_reporting')
    def test_table_dictize_with_metabase_mapping(self):
        """Test table_dictize with MetabaseMapping object"""
        user = factories.User()

        mapping = MetabaseMapping(
            user_id=user['id'],
            platform_uuid='12345678-1234-1234-1234-123456789012',
            email=user['email'],
            group_ids='group1;group2',
            collection_ids='col1;col2',
            created=datetime.datetime(2023, 1, 1, 12, 0, 0),
            modified=datetime.datetime(2023, 1, 2, 12, 0, 0)
        )

        model.Session.add(mapping)
        model.Session.commit()

        result = table_dictize(mapping, {})

        assert isinstance(result, dict)
        assert result['user_id'] == user['id']
        assert result['platform_uuid'] == '12345678-1234-1234-1234-123456789012'
        assert result['email'] == user['email']
        assert result['group_ids'] == 'group1;group2'
        assert result['collection_ids'] == 'col1;col2'
        assert result['created'] == '2023-01-01T12:00:00'
        assert result['modified'] == '2023-01-02T12:00:00'

    def test_table_dictize_with_row_object(self):
        """Test table_dictize with Row object"""
        try:
            from sqlalchemy.engine import Row
        except ImportError:
            try:
                from sqlalchemy.engine.result import RowProxy as Row
            except ImportError:
                from sqlalchemy.engine.base import RowProxy as Row

        # Mock a Row object
        mock_row = mock.Mock(spec=Row)
        mock_row.keys.return_value = ['user_id', 'email', 'created']
        mock_row.user_id = 'test-user'
        mock_row.email = 'test@example.com'
        mock_row.created = datetime.datetime(2023, 1, 1, 12, 0, 0)

        result = table_dictize(mock_row, {})

        assert result['user_id'] == 'test-user'
        assert result['email'] == 'test@example.com'
        assert result['created'] == '2023-01-01T12:00:00'
