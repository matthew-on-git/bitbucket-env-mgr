"""Unit tests for main function integration in manage_bitbucket_env.py."""
# pylint: disable=unused-argument
import unittest
from unittest.mock import patch, Mock
from typing import Optional

from manage_bitbucket_env import main

class TestMainFunction(unittest.TestCase):
    """Test main function integration."""
    # pylint: disable=attribute-defined-outside-init
    mock_logger: Optional[Mock] = None

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()

    @patch('manage_bitbucket_env.arg_parser')
    @patch('manage_bitbucket_env.load_dotenv')
    @patch('os.environ.get')
    @patch('manage_bitbucket_env.HTTPBasicAuth')
    @patch('manage_bitbucket_env.export_variables')
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def test_main_export_variables(self, mock_export, mock_auth, mock_env_get,
                                  mock_load_dotenv, mock_arg_parser):
        """Test main function with export variables."""
        mock_args = Mock()
        mock_args.output = 'test_output.json'
        mock_args.workspace = 'test-workspace'
        mock_args.repo_slug = 'test-repo'
        mock_args.deployment_name = 'test-deployment'
        mock_arg_parser.return_value = mock_args
        env_dict = {
            'BITBUCKET_USERNAME': 'test_user',
            'BITBUCKET_APP_PASSWORD': 'test_password'
        }
        mock_env_get.side_effect = env_dict.get
        mock_auth_instance = Mock()
        mock_auth.return_value = mock_auth_instance
        main(self.mock_logger)
        mock_export.assert_called_once_with(
            workspace='test-workspace',
            repo_slug='test-repo',
            deployment_name='test-deployment',
            output_file='test_output.json',
            auth=mock_auth_instance,
            logger=self.mock_logger
        )

    @patch('manage_bitbucket_env.arg_parser')
    @patch('manage_bitbucket_env.load_dotenv')
    @patch('os.environ.get')
    def test_main_missing_credentials(self, mock_env_get, mock_load_dotenv, mock_arg_parser):
        """Test main function with missing credentials."""
        mock_args = Mock()
        mock_args.output = 'test_output.json'
        mock_arg_parser.return_value = mock_args
        mock_env_get.return_value = None
        with self.assertRaises(SystemExit):
            main(self.mock_logger)

if __name__ == '__main__':
    unittest.main()
