"""Unit tests for update_vars logic in manage_bitbucket_env.py."""
# pylint: disable=duplicate-code
from manage_bitbucket_env import update_vars
import unittest
from unittest.mock import patch, Mock
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestUpdateVars(unittest.TestCase):
    """Test variable update functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger: Mock = Mock()
        self.auth: Mock = Mock()
        self.workspace: str = 'ws'
        self.repo_slug: str = 'repo'
        self.env_uuid: str = 'uuid-123'

    @patch('manage_bitbucket_env.requests.put')
    def test_update_existing(self, mock_put):
        """Test updating an existing variable."""
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_put.return_value = mock_resp
        existing_vars = [{"key": "A", "uuid": "u1", "value": "old", "secured": False}]
        new_var = {"key": "A", "value": "new", "secured": False}
        update_vars(
            self.workspace, self.repo_slug, self.env_uuid,
            existing_vars, new_var, self.auth, self.logger
        )
        mock_put.assert_called_once()
        call_args = mock_put.call_args
        self.assertIn("u1", call_args[0][0])

    @patch('manage_bitbucket_env.requests.post')
    def test_update_new(self, mock_post):
        """Test creating a new variable."""
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp
        existing_vars = []
        new_var = {"key": "B", "value": "val", "secured": False}
        update_vars(
            self.workspace, self.repo_slug, self.env_uuid,
            existing_vars, new_var, self.auth, self.logger
        )
        mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main() 