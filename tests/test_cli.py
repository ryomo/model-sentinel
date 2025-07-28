"""
Tests for model_sentinel.cli module.
"""
import unittest
from unittest.mock import Mock, patch, call
import sys
from io import StringIO

from model_sentinel import cli


class TestCLI(unittest.TestCase):
    """Test cases for CLI functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Store original argv to restore later
        self.original_argv = sys.argv.copy()

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Restore original argv
        sys.argv = self.original_argv

    @patch('model_sentinel.cli.Verify')
    def test_delete_option(self, mock_verify_class):
        """Test --delete option."""
        mock_verify = Mock()
        mock_verify.delete_hash_file.return_value = True
        mock_verify_class.return_value = mock_verify

        sys.argv = ['model-sentinel', '--delete']

        with patch('builtins.print') as mock_print:
            cli.main()

        mock_verify.delete_hash_file.assert_called_once()
        mock_print.assert_called_with("Hash file deleted.")

    @patch('model_sentinel.cli.Verify')
    def test_delete_option_failure(self, mock_verify_class):
        """Test --delete option when deletion fails."""
        mock_verify = Mock()
        mock_verify.delete_hash_file.return_value = False
        mock_verify_class.return_value = mock_verify

        sys.argv = ['model-sentinel', '--delete']

        with patch('builtins.print') as mock_print:
            cli.main()

        mock_verify.delete_hash_file.assert_called_once()
        mock_print.assert_called_with("Failed to delete hash file.")

    @patch('model_sentinel.cli.Verify')
    def test_list_verified_option(self, mock_verify_class):
        """Test --list-verified option."""
        mock_verify = Mock()
        mock_verify_class.return_value = mock_verify

        sys.argv = ['model-sentinel', '--list-verified']

        cli.main()

        mock_verify.list_verified_hashes.assert_called_once()

    @patch('argparse.ArgumentParser.print_help')
    def test_default_help_behavior(self, mock_print_help):
        """Test default behavior shows help when no model is specified."""
        sys.argv = ['model-sentinel']

        cli.main()

        # Should call print_help when no model is specified
        mock_print_help.assert_called_once()

    @patch('model_sentinel.cli.verify_hf_model')
    def test_custom_hf_repo(self, mock_verify_hf):
        """Test custom Hugging Face repository."""
        mock_verify_hf.return_value = True

        sys.argv = ['model-sentinel', '--hf', 'custom/repo', '--revision', 'v1.0']

        with patch('builtins.print') as mock_print:
            cli.main()

        mock_verify_hf.assert_called_once_with("custom/repo", "v1.0")

    @patch('model_sentinel.cli.verify_hf_model')
    def test_hf_model_not_verified(self, mock_verify_hf):
        """Test when Hugging Face model is not verified."""
        mock_verify_hf.return_value = False

        sys.argv = ['model-sentinel', '--hf', 'test/repo']

        with patch('builtins.print') as mock_print:
            cli.main()

        mock_verify_hf.assert_called_once_with("test/repo", "main")

        # Check error messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        self.assertTrue(any("Repository test/repo at revision main is not verified." in call for call in print_calls))
        self.assertTrue(any("Please verify all remote files in the repository before proceeding." in call for call in print_calls))

    @patch('model_sentinel.cli.verify_local_model')
    def test_local_model_verified(self, mock_verify_local):
        """Test local model verification."""
        mock_verify_local.return_value = True

        sys.argv = ['model-sentinel', '--local', '/path/to/model']

        with patch('builtins.print') as mock_print:
            cli.main()

        mock_verify_local.assert_called_once_with('/path/to/model')

        # Check that it prints the local model info
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        self.assertTrue(any("Verifying local model: /path/to/model" in call for call in print_calls))

    @patch('model_sentinel.cli.verify_local_model')
    def test_local_model_not_verified(self, mock_verify_local):
        """Test when local model is not verified."""
        mock_verify_local.return_value = False

        sys.argv = ['model-sentinel', '--local', '/path/to/model']

        with patch('builtins.print') as mock_print:
            cli.main()

        mock_verify_local.assert_called_once_with('/path/to/model')

        # Check error messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        self.assertTrue(any("Local model /path/to/model is not verified." in call for call in print_calls))
        self.assertTrue(any("Please verify all files in the model directory before proceeding." in call for call in print_calls))

    def test_gui_option_not_tested(self):
        """Note: GUI functionality is not tested in unit tests to avoid server startup."""
        # GUI tests are skipped because they would start a Gradio server
        # which is not appropriate for unit testing
        pass


class TestCLIHostPortArguments(unittest.TestCase):
    """Test cases for CLI host and port argument parsing."""

    def test_cli_argument_parsing(self):
        """Test CLI argument parsing for host and port options."""
        import argparse

        # Recreate the parser logic from cli.py
        parser = argparse.ArgumentParser(description="Model Sentinel CLI")
        parser.add_argument("--gui", action="store_true", help="Launch GUI interface")
        parser.add_argument(
            "--host",
            type=str,
            default="127.0.0.1",
            help="GUI server host address (default: 127.0.0.1)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=7860,
            help="GUI server port (default: 7860)",
        )

        # Test parsing with all arguments
        args = parser.parse_args(["--gui", "--host", "0.0.0.0", "--port", "8080"])
        self.assertTrue(args.gui)
        self.assertEqual(args.host, "0.0.0.0")
        self.assertEqual(args.port, 8080)

        # Test parsing with GUI only
        args = parser.parse_args(["--gui"])
        self.assertTrue(args.gui)
        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 7860)

    @patch('model_sentinel.gui.launch_verification_gui')
    def test_cli_to_gui_with_host_port(self, mock_launch):
        """Test that CLI passes host and port to GUI correctly."""
        with patch('sys.argv', ['model-sentinel', '--gui', '--host', '0.0.0.0', '--port', '9000']):
            try:
                cli.main()
            except SystemExit:
                pass  # SystemExit is expected but not required

        mock_launch.assert_called_once_with(host='0.0.0.0', port=9000)

    @patch('model_sentinel.gui.launch_verification_gui')
    def test_cli_to_gui_with_repo(self, mock_launch):
        """Test CLI to GUI integration with repo specification."""
        test_args = [
            'model-sentinel', '--gui', '--hf', 'test/repo',
            '--revision', 'v1.0', '--host', '192.168.1.100', '--port', '8080'
        ]

        with patch('sys.argv', test_args):
            try:
                cli.main()
            except SystemExit:
                pass  # SystemExit is expected but not required

        mock_launch.assert_called_once_with(
            repo_id='test/repo',
            revision='v1.0',
            host='192.168.1.100',
            port=8080
        )

    @patch('model_sentinel.gui.launch_verification_gui')
    def test_cli_to_gui_defaults(self, mock_launch):
        """Test CLI to GUI with default values."""
        with patch('sys.argv', ['model-sentinel', '--gui']):
            try:
                cli.main()
            except SystemExit:
                pass  # SystemExit is expected but not required

        mock_launch.assert_called_once_with(host="127.0.0.1", port=7860)


if __name__ == '__main__':
    unittest.main()
