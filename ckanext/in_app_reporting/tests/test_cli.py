import pytest
from unittest import mock
from ckan.tests import factories
from ckan.cli.cli import ckan


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "in_app_reporting")
class TestMetabaseCli:

    def test_metabase_add_success(self, cli):
        user = factories.User()
        args = [
            "metabase",
            "add",
            user["id"],
            "--group_ids=group1;;group2",
            "--collection_ids=1;;2",
        ]
        with mock.patch("ckanext.in_app_reporting.utils.metabase_mapping_create", return_value={"ok": True}):
            result = cli.invoke(ckan, args)
        assert result.exit_code == 0
        assert f"Metabase mapping created successfully for user_id: {user['id']}" in result.output

    def test_metabase_add_missing_args(self, cli):
        result = cli.invoke(ckan, ["metabase", "add"])  # missing required args
        assert result.exit_code != 0

    def test_metabase_add_invalid_uuid_error_bubbled(self, cli):
        user = factories.User()
        args = [
            "metabase",
            "add",
            user["id"],
            "--group_ids=group1",
            "--collection_ids=1",
        ]
        with mock.patch("ckanext.in_app_reporting.utils.metabase_mapping_create", side_effect=Exception("boom")):
            result = cli.invoke(ckan, args)
        assert result.exit_code != 0

    def test_metabase_update_success(self, cli):
        user = factories.User()
        # Ensure mapping exists, then run update
        from ckan.plugins.toolkit import get_action
        get_action("metabase_mapping_create")({"ignore_auth": True}, {
            "user_id": user["id"],
            "platform_uuid": "12345678-1234-1234-1234-123456789012",
            "group_ids": ["g1", "g2"],
            "collection_ids": ["c1", "c2"],
        })

        args_update = [
            "metabase",
            "update",
            user["id"],
            "--group_ids=x1;;x2",
            "--collection_ids=1;;2",
        ]
        with mock.patch("ckanext.in_app_reporting.utils.metabase_mapping_update", return_value={"ok": True}):
            result = cli.invoke(ckan, args_update)
        assert result.exit_code == 0
        assert f"Metabase mapping updated successfully for user_id: {user['id']}" in result.output

    def test_metabase_update_missing_args(self, cli):
        result = cli.invoke(ckan, ["metabase", "update"])  # missing required args
        assert result.exit_code != 0

    def test_metabase_remove_success(self, cli):
        user = factories.User()
        from ckan.plugins.toolkit import get_action
        get_action("metabase_mapping_create")({"ignore_auth": True}, {
            "user_id": user["id"],
            "platform_uuid": "12345678-1234-1234-1234-123456789012",
            "group_ids": ["g1", "g2"],
            "collection_ids": ["1", "2"],
        })

        with mock.patch("ckanext.in_app_reporting.utils.metabase_mapping_delete", return_value={"message": "ok"}):
            result = cli.invoke(ckan, ["metabase", "remove", user["id"]])
        assert result.exit_code == 0
        assert f"Metabase mapping removed successfully for user_id: {user['id']}" in result.output

    def test_metabase_remove_not_found(self, cli):
        result = cli.invoke(ckan, ["metabase", "remove", "non-existent-id"])  # no mapping exists
        assert result.exit_code != 0 