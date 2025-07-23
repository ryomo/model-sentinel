"""
Tests for model_sentinel.verify.verify module.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from model_sentinel.verify.verify import Verify


class TestVerify(unittest.TestCase):
    """Test cases for Verify class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.verify = Verify()
        # Use temporary file for testing to avoid affecting real files
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_hash_file = self.temp_dir / "test_model_sentinel.json"
        self.verify.verified_hashes_file = self.test_hash_file

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Clean up temporary files
        if self.test_hash_file.exists():
            self.test_hash_file.unlink()
        if self.temp_dir.exists():
            self.temp_dir.rmdir()

    def test_init(self):
        """Test Verify class initialization."""
        verify_instance = Verify()
        self.assertIsInstance(verify_instance.verified_hashes_file, Path)
        self.assertEqual(verify_instance.verified_hashes_file.name, ".model-sentinel.json")

    def test_load_verified_hashes_file_not_exists(self):
        """Test loading verified hashes when file doesn't exist."""
        result = self.verify.load_verified_hashes()
        self.assertEqual(result, {})

    def test_load_verified_hashes_file_exists(self):
        """Test loading verified hashes when file exists."""
        test_data = {
            "test_repo": {
                "files": {"test.py": "test_hash"},
                "last_checked": "2025-07-23T00:00:00Z"
            }
        }

        # Create test file
        with open(self.test_hash_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        result = self.verify.load_verified_hashes()
        self.assertEqual(result, test_data)

    def test_save_verified_hashes(self):
        """Test saving verified hashes to file."""
        test_data = {
            "test_repo": {
                "files": {"test.py": "test_hash"},
                "last_checked": "2025-07-23T00:00:00Z"
            }
        }

        self.verify.save_verified_hashes(test_data)

        # Verify file was created and contains correct data
        self.assertTrue(self.test_hash_file.exists())
        with open(self.test_hash_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, test_data)

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
        data = {"test_repo": {"files": {}}}

        with patch.object(self.verify, 'prompt_user_verification', return_value=True):
            with patch('builtins.print') as mock_print:
                result = self.verify.verify_file("test.py", "new_hash", "content", data, "test_repo")

                self.assertTrue(result)
                self.assertEqual(data["test_repo"]["files"]["test.py"], "new_hash")
                mock_print.assert_called_with("Trust confirmed. Hash updated.")

    def test_verify_file_user_rejects(self):
        """Test verify_file when user rejects the file."""
        data = {"test_repo": {"files": {}}}

        with patch.object(self.verify, 'prompt_user_verification', return_value=False):
            with patch('builtins.print') as mock_print:
                result = self.verify.verify_file("test.py", "new_hash", "content", data, "test_repo")

                self.assertFalse(result)
                self.assertNotIn("test.py", data["test_repo"]["files"])
                mock_print.assert_called_with("Trust not confirmed. Please review the file changes.")

    def test_delete_hash_file_exists(self):
        """Test deleting hash file when it exists."""
        # Create test file
        self.test_hash_file.touch()
        self.assertTrue(self.test_hash_file.exists())

        result = self.verify.delete_hash_file()

        self.assertTrue(result)
        self.assertFalse(self.test_hash_file.exists())

    def test_delete_hash_file_not_exists(self):
        """Test deleting hash file when it doesn't exist."""
        self.assertFalse(self.test_hash_file.exists())

        result = self.verify.delete_hash_file()

        self.assertTrue(result)  # Should still return True

    @patch('builtins.print')
    def test_list_verified_hashes_empty(self, mock_print):
        """Test listing verified hashes when none exist."""
        with patch.object(self.verify, 'load_verified_hashes', return_value={}):
            self.verify.list_verified_hashes()
            mock_print.assert_called_with("No verified hashes found.")

    @patch('builtins.print')
    def test_list_verified_hashes_with_data(self, mock_print):
        """Test listing verified hashes with data."""
        test_data = {
            "test_repo": {
                "revision": "main",
                "model_hash": "model_hash_value",
                "files": {
                    "test1.py": "hash1",
                    "test2.py": "hash2"
                }
            }
        }

        with patch.object(self.verify, 'load_verified_hashes', return_value=test_data):
            self.verify.list_verified_hashes()

            # Check that expected content was printed
            calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertIn("=== Verified Hashes Summary ===", calls)
            self.assertTrue(any("Repository: test_repo" in call for call in calls))
            self.assertTrue(any("Revision: main" in call for call in calls))


if __name__ == '__main__':
    unittest.main()
