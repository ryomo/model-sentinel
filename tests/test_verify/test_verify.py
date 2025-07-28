"""
Tests for model_sentinel.verify.verify module.
"""
import json
import tempfile
import unittest
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from model_sentinel.verify.verify import Verify
from model_sentinel.directory.manager import DirectoryManager


class TestVerify(unittest.TestCase):
    """Test cases for Verify class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.verify = Verify()
        # Use temporary directory for testing to avoid affecting real files
        self.temp_dir = Path(tempfile.mkdtemp())
        # Override storage to use test directory
        self.verify.storage = DirectoryManager(self.temp_dir / ".model-sentinel")

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Clean up temporary files
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test Verify class initialization."""
        verify_instance = Verify()
        self.assertIsInstance(verify_instance.directory_manager, DirectoryManager)

    def test_storage_integration(self):
        """Test storage system integration."""
        # Create a test model directory
        model_dir = self.temp_dir / "test_model"
        model_dir.mkdir(parents=True)

        # Test metadata operations
        test_metadata = {
            "model_hash": "test_hash",
            "last_verified": "2025-07-28T00:00:00Z",
            "files": {
                "test.py": {
                    "hash": "file_hash",
                    "size": 100,
                    "verified_at": "2025-07-28T00:00:00Z"
                }
            }
        }

        self.verify.directory_manager.save_metadata(model_dir, test_metadata)
        loaded_metadata = self.verify.directory_manager.load_metadata(model_dir)
        self.assertEqual(loaded_metadata["model_hash"], "test_hash")

    @patch('builtins.input', return_value='y')
    @patch('pydoc.pager')
    def test_prompt_user_verification_yes(self, mock_pager, mock_input):
        """Test user verification prompt with 'yes' response."""
        result = self.verify.prompt_user_verification("test_file.py", "test content")
        self.assertTrue(result)
        mock_pager.assert_called_once()

    @patch('builtins.input', return_value='n')
    @patch('pydoc.pager')
    def test_prompt_user_verification_no(self, mock_pager, mock_input):
        """Test user verification prompt with 'no' response."""
        result = self.verify.prompt_user_verification("test_file.py", "test content")
        self.assertFalse(result)
        mock_pager.assert_called_once()

    @patch('builtins.input', return_value='yes')
    @patch('pydoc.pager')
    def test_prompt_user_verification_yes_full(self, mock_pager, mock_input):
        """Test user verification prompt with full 'yes' response."""
        result = self.verify.prompt_user_verification("test_file.py", "test content")
        self.assertTrue(result)

    def test_verify_file_user_confirms(self):
        """Test verify_file when user confirms the file."""
        model_dir = self.temp_dir / "test_model"

        with patch.object(self.verify, 'prompt_user_verification', return_value=True):
            result = self.verify.verify_file("test.py", "new_hash", "content", model_dir)
            self.assertTrue(result)

    def test_verify_file_user_rejects(self):
        """Test verify_file when user rejects the file."""
        model_dir = self.temp_dir / "test_model"

        with patch.object(self.verify, 'prompt_user_verification', return_value=False):
            result = self.verify.verify_file("test.py", "new_hash", "content", model_dir)
            self.assertFalse(result)

    def test_delete_hash_file_directory_exists(self):
        """Test deleting storage directory when it exists."""
        # Create storage directory
        self.verify.directory_manager.ensure_directories()
        self.assertTrue(self.verify.directory_manager.base_dir.exists())

        result = self.verify.delete_hash_file()

        self.assertTrue(result)
        self.assertFalse(self.verify.directory_manager.base_dir.exists())

    def test_delete_hash_file_directory_not_exists(self):
        """Test deleting storage directory when it doesn't exist."""
        self.assertFalse(self.verify.directory_manager.base_dir.exists())

        result = self.verify.delete_hash_file()

        self.assertTrue(result)  # Should still return True

    @patch('builtins.print')
    def test_list_verified_hashes_empty(self, mock_print):
        """Test listing verified hashes when none exist."""
        self.verify.list_verified_hashes()
        mock_print.assert_called_with("No verified models found.")

    @patch('builtins.print')
    def test_list_verified_hashes_with_data(self, mock_print):
        """Test listing verified hashes with data."""
        # Create test model data in storage system
        test_model_dir = self.verify.directory_manager.base_dir / "hf" / "test" / "repo@main"
        test_model_dir.mkdir(parents=True)

        test_metadata = {
            "model_hash": "model_hash_value",
            "last_verified": "2025-07-28T00:00:00Z",
            "files": {
                "test1.py": {"hash": "hash1", "size": 100},
                "test2.py": {"hash": "hash2", "size": 200}
            }
        }
        self.verify.directory_manager.save_metadata(test_model_dir, test_metadata)

        # Register model in registry
        self.verify.directory_manager.register_model("hf", "test/repo@main")

        self.verify.list_verified_hashes()

        # Check that expected content was printed
        calls = [call[0][0] for call in mock_print.call_args_list]
        self.assertIn("=== Verified Models Summary ===", calls)
        self.assertTrue(any("Model: hf/test/repo@main" in call for call in calls))


if __name__ == '__main__':
    unittest.main()
