"""Unit tests for Bitbucket API logic in manage_bitbucket_env.py."""
from manage_bitbucket_env import get_environment_uuid, get_variables
import unittest
from unittest.mock import patch, Mock
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestAPI(unittest.TestCase):
    """Test API-related functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger: Mock = Mock()
        self.auth: Mock = Mock()
        self.workspace: str = 'ws'
        self.repo_slug: str = 'repo'
        self.deployment_name: str = 'env'
        self.env_uuid: str = 'uuid-123'

    @patch('manage_bitbucket_env.requests.get')
    def test_get_environment_uuid_found(self, mock_get):
        """Test successful environment UUID retrieval."""
        mock_resp = Mock()
        mock_resp.json.return_value = {
            "values": [{"name": "env", "uuid": "uuid-123"}]
        }
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        uuid = get_environment_uuid(
            self.workspace, self.repo_slug, self.deployment_name,
            self.auth, self.logger
        )
        self.assertEqual(uuid, 'uuid-123')
        mock_get.assert_called_once()

    @patch('manage_bitbucket_env.requests.get')
    def test_get_environment_uuid_not_found(self, mock_get):
        """Test environment UUID retrieval when environment not found."""
        mock_resp = Mock()
        mock_resp.json.return_value = {
            "values": [{"name": "other", "uuid": "uuid-999"}]
        }
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        with self.assertRaises(ValueError):
            get_environment_uuid(
                self.workspace, self.repo_slug, self.deployment_name,
                self.auth, self.logger
            )

    @patch('manage_bitbucket_env.requests.get')
    def test_get_variables(self, mock_get):
        """Test successful variable retrieval."""
        mock_resp = Mock()
        mock_resp.json.return_value = {
            "values": [{"key": "A", "value": "1", "secured": False}]
        }
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        result_vars = get_variables(
            self.workspace, self.repo_slug, self.env_uuid,
            self.auth, self.logger
        )
        self.assertEqual(result_vars[0]["key"], "A")

if __name__ == '__main__':
    unittest.main() 