"""Unit tests for export/import logic in manage_bitbucket_env.py."""
# pylint: disable=duplicate-code
import unittest
from unittest.mock import patch, Mock
import os
import tempfile
import json
from typing import Optional

from manage_bitbucket_env import (
    export_variables, export_all_variables, export_secure_keys, import_variables
)

class TestExportImport(unittest.TestCase):
    """Test export and import functionality."""
    # pylint: disable=attribute-defined-outside-init
    logger: Optional[Mock] = None
    auth: Optional[Mock] = None
    workspace: Optional[str] = None
    repo_slug: Optional[str] = None
    deployment_name: Optional[str] = None
    env_uuid: Optional[str] = None

    def setUp(self):
        """Set up test fixtures."""
        self.logger: Mock = Mock()
        self.auth: Mock = Mock()
        self.workspace: str = 'ws'
        self.repo_slug: str = 'repo'
        self.deployment_name: str = 'env'
        self.env_uuid: str = 'uuid-123'

    @patch('manage_bitbucket_env.get_environment_uuid')
    @patch('manage_bitbucket_env.get_variables')
    def test_export_variables(self, mock_get_vars, mock_get_uuid):
        """Test successful export of non-secured variables."""
        mock_get_uuid.return_value = self.env_uuid
        mock_get_vars.return_value = [
            {"key": "A", "value": "1", "secured": False},
            {"key": "B", "value": "2", "secured": True}
        ]
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            fname = tf.name
        try:
            export_variables(
                self.workspace, self.repo_slug, self.deployment_name,
                fname, self.auth, self.logger
            )
            with open(fname, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["key"], "A")
        finally:
            os.unlink(fname)

    @patch('manage_bitbucket_env.get_environment_uuid')
    @patch('manage_bitbucket_env.get_variables')
    def test_export_all_variables(self, mock_get_vars, mock_get_uuid):
        """Test successful export of all variables."""
        mock_get_uuid.return_value = self.env_uuid
        mock_get_vars.return_value = [
            {"key": "A", "value": "1", "secured": False},
            {"key": "B", "value": "2", "secured": True}
        ]
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            fname = tf.name
        try:
            export_all_variables(
                self.workspace, self.repo_slug, self.deployment_name,
                fname, self.auth, self.logger
            )
            with open(fname, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(len(data), 2)
            test_var = next(v for v in data if v["key"] == "A")
            self.assertEqual(test_var["value"], "1")
            self.assertFalse(test_var["secured"])
            secure_var = next(v for v in data if v["key"] == "B")
            self.assertEqual(secure_var["value"], "")
            self.assertTrue(secure_var["secured"])
        finally:
            os.unlink(fname)

    @patch('manage_bitbucket_env.get_environment_uuid')
    @patch('manage_bitbucket_env.get_variables')
    def test_export_secure_keys(self, mock_get_vars, mock_get_uuid):
        """Test successful export of secure keys."""
        mock_get_uuid.return_value = self.env_uuid
        mock_get_vars.return_value = [
            {"key": "A", "secured": False},
            {"key": "B", "secured": True},
            {"key": "C", "secured": True}
        ]
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            fname = tf.name
        try:
            export_secure_keys(
                self.workspace, self.repo_slug, self.deployment_name,
                fname, self.auth, self.logger
            )
            with open(fname, encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("B", data)
            self.assertIn("C", data)
            self.assertNotIn("A", data)
        finally:
            os.unlink(fname)

    @patch('manage_bitbucket_env.get_environment_uuid')
    @patch('manage_bitbucket_env.get_variables')
    @patch('manage_bitbucket_env.update_vars')
    def test_import_variables(self, mock_update, mock_get_vars, mock_get_uuid):
        """Test successful import of variables."""
        mock_get_uuid.return_value = self.env_uuid
        mock_get_vars.return_value = []
        test_vars = [
            {"key": "A", "value": "1", "secured": False},
            {"key": "B", "value": "2", "secured": True}
        ]
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding="utf-8") as tf:
            json.dump(test_vars, tf)
            fname = tf.name
        try:
            import_variables(
                self.workspace, self.repo_slug, self.deployment_name,
                fname, False, self.auth, self.logger
            )
            self.assertEqual(mock_update.call_count, 1)
            call_args = mock_update.call_args[1]
            self.assertEqual(call_args['var']["key"], "A")
        finally:
            os.unlink(fname)

if __name__ == '__main__':
    unittest.main()
