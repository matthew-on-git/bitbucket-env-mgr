import unittest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manage_bitbucket_env import arg_parser

class TestArgParser(unittest.TestCase):
    def test_export_args(self):
        test_args = [
            'prog', '-w', 'ws', '-r', 'repo', '-d', 'env', '-o', 'out.json'
        ]
        with patch.object(sys, 'argv', test_args):
            args = arg_parser()
            self.assertEqual(args.workspace, 'ws')
            self.assertEqual(args.repo_slug, 'repo')
            self.assertEqual(args.deployment_name, 'env')
            self.assertEqual(args.output, 'out.json')

    def test_import_args(self):
        test_args = [
            'prog', '-w', 'ws', '-r', 'repo', '-d', 'env', '-i', 'in.json'
        ]
        with patch.object(sys, 'argv', test_args):
            args = arg_parser()
            self.assertEqual(args.import_file, 'in.json')

    def test_mutually_exclusive(self):
        test_args = [
            'prog', '-w', 'ws', '-r', 'repo', '-d', 'env'
        ]
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit):
                arg_parser()

if __name__ == '__main__':
    unittest.main() 