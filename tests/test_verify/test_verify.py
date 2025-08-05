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


class TestVerifyBusinessLogic(unittest.TestCase):
    """Tests for business logic methods in Verify class after Issue #13 refactoring."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(self.cleanup_temp_dir)

    def cleanup_temp_dir(self):
        """Clean up temporary directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch('model_sentinel.target.hf.TargetHF')
    def test_verify_hf_model_no_changes(self, mock_target_hf_class):
        """Test verify_hf_model when no changes are detected."""
        # Setup mock
        mock_target = Mock()
        mock_target_hf_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = None  # No changes

        verify = Verify()
        result = verify.verify_hf_model("test/model")

        # Assertions
        mock_target.detect_model_changes.assert_called_once_with("test/model", "main")

        expected_result = {
            "target_type": "hf",
            "repo_id": "test/model",
            "revision": "main",
            "status": "success",
            "model_hash_changed": False,
            "new_model_hash": None,
            "files_verified": True,
            "message": "No changes detected in the model hash.",
            "files_info": [],
            "display_info": [
                "**Repository:** test/model",
                "**Revision:** main"
            ]
        }
        self.assertEqual(result, expected_result)

    @patch('model_sentinel.target.hf.TargetHF')
    def test_verify_hf_model_with_changes(self, mock_target_hf_class):
        """Test verify_hf_model when changes are detected."""
        # Setup mock
        mock_target = Mock()
        mock_target_hf_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash_123"
        mock_target.get_files_for_verification.return_value = [
            {"filename": "modeling.py", "hash": "file_hash", "content": "# Test content"}
        ]

        verify = Verify()
        result = verify.verify_hf_model("test/model")

        # Assertions
        mock_target.detect_model_changes.assert_called_once_with("test/model", "main")
        mock_target.get_files_for_verification.assert_called_once_with("test/model", "main")

        expected_result = {
            "target_type": "hf",
            "repo_id": "test/model",
            "revision": "main",
            "status": "success",
            "model_hash_changed": True,
            "new_model_hash": "new_hash_123",
            "files_verified": False,
            "message": "Found 1 files that need verification.",
            "files_info": [
                {"filename": "modeling.py", "hash": "file_hash", "content": "# Test content"}
            ],
            "display_info": [
                "**Repository:** test/model",
                "**Revision:** main"
            ]
        }
        self.assertEqual(result, expected_result)

    def test_verify_local_model_directory_not_exists(self):
        """Test verify_local_model when directory doesn't exist."""
        non_existent_dir = "/path/to/nonexistent"

        verify = Verify()

        with self.assertRaises(FileNotFoundError) as context:
            verify.verify_local_model(non_existent_dir)

        self.assertIn("does not exist", str(context.exception))

    @patch('model_sentinel.target.local.TargetLocal')
    def test_verify_local_model_success(self, mock_target_local_class):
        """Test verify_local_model with successful operation."""
        # Create temporary model directory
        model_dir = self.temp_dir / "test_model"
        model_dir.mkdir()

        # Setup mock
        mock_target = Mock()
        mock_target_local_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "local_hash_456"
        mock_target.get_files_for_verification.return_value = [
            {"filename": "script.py", "hash": "script_hash", "content": "# Script content"}
        ]

        verify = Verify()
        result = verify.verify_local_model(str(model_dir))

        # Assertions
        mock_target.detect_model_changes.assert_called_once_with(model_dir)
        mock_target.get_files_for_verification.assert_called_once_with(model_dir)

        expected_result = {
            "target_type": "local",
            "model_dir": str(model_dir),
            "status": "success",
            "model_hash_changed": True,
            "new_model_hash": "local_hash_456",
            "files_verified": False,
            "message": "Found 1 files that need verification.",
            "files_info": [
                {"filename": "script.py", "hash": "script_hash", "content": "# Script content"}
            ],
            "display_info": [
                f"**Model Directory:** {model_dir}"
            ]
        }
        self.assertEqual(result, expected_result)

    def test_save_verification_results_no_changes(self):
        """Test save_verification_results when no changes detected."""
        verify = Verify()
        verification_result = {
            "model_hash_changed": False,
            "message": "No changes detected"
        }
        approved_files = []

        result = verify.save_verification_results(verification_result, approved_files)

        self.assertEqual(result, "No changes to save.")

    @patch('model_sentinel.verify.verify.datetime')
    def test_save_verification_results_hf_success(self, mock_datetime):
        """Test save_verification_results with HuggingFace model success case."""
        # Setup mock datetime
        mock_now = Mock()
        mock_now.isoformat.return_value = "2025-08-05T12:00:00Z"
        mock_datetime.now.return_value = mock_now

        verify = Verify()

        # Mock directory manager methods
        mock_model_dir = Mock()
        verify.directory_manager.get_hf_model_dir = Mock(return_value=mock_model_dir)
        verify.directory_manager.load_metadata = Mock(return_value={"files": {}})
        verify.directory_manager.save_metadata = Mock()
        verify.directory_manager.save_file_content = Mock()
        verify.directory_manager.register_model = Mock()
        verify.update_model_hash = Mock()
        verify.get_model_key_from_result = Mock(return_value="hf/test/model@main")

        verification_result = {
            "model_hash_changed": True,
            "target_type": "hf",
            "repo_id": "test/model",
            "revision": "main",
            "new_model_hash": "abc123",
            "files_info": [
                {"filename": "modeling.py", "hash": "def456", "content": "# Test content"}
            ]
        }
        approved_files = ["modeling.py"]

        # Test function
        result = verify.save_verification_results(verification_result, approved_files)

        # Assertions
        verify.get_model_key_from_result.assert_called_once_with(verification_result)
        verify.directory_manager.get_hf_model_dir.assert_called_once_with("test/model", "main")
        verify.update_model_hash.assert_called_once_with(mock_model_dir, "abc123")
        verify.directory_manager.save_file_content.assert_called_once_with(
            mock_model_dir, "modeling.py", "# Test content"
        )
        verify.directory_manager.register_model.assert_called_once_with("hf", "test/model@main")

        self.assertEqual(result, "✅ Verification completed! 1 files approved and saved.")

    @patch('model_sentinel.verify.verify.datetime')
    def test_save_verification_results_local_success(self, mock_datetime):
        """Test save_verification_results with local model success case."""
        # Setup mock datetime
        mock_now = Mock()
        mock_now.isoformat.return_value = "2025-08-05T12:00:00Z"
        mock_datetime.now.return_value = mock_now

        verify = Verify()

        # Mock directory manager methods
        mock_model_dir = Mock()
        verify.directory_manager.get_local_model_dir = Mock(return_value=mock_model_dir)
        verify.directory_manager.load_metadata = Mock(return_value={"files": {}})
        verify.directory_manager.save_metadata = Mock()
        verify.directory_manager.save_file_content = Mock()
        verify.directory_manager.register_model = Mock()
        verify.update_model_hash = Mock()
        verify.get_model_key_from_result = Mock(return_value="local/test_model_hash")

        verification_result = {
            "model_hash_changed": True,
            "target_type": "local",
            "model_dir": "/path/to/model",
            "new_model_hash": "xyz999",
            "files_info": [
                {"filename": "script.py", "hash": "abc123", "content": "# Script content"}
            ]
        }
        approved_files = ["script.py"]

        # Test function
        result = verify.save_verification_results(verification_result, approved_files)

        # Assertions
        verify.get_model_key_from_result.assert_called_once_with(verification_result)
        verify.directory_manager.get_local_model_dir.assert_called_once_with(Path("/path/to/model"))
        verify.update_model_hash.assert_called_once_with(mock_model_dir, "xyz999")
        verify.directory_manager.save_file_content.assert_called_once_with(
            mock_model_dir, "script.py", "# Script content"
        )
        verify.directory_manager.register_model.assert_called_once_with("local", "test_model_hash", original_path="/path/to/model")

        self.assertEqual(result, "✅ Verification completed! 1 files approved and saved.")

    def test_save_verification_results_error_handling(self):
        """Test save_verification_results error handling."""
        verify = Verify()

        # Mock get_model_key_from_result to raise exception
        verify.get_model_key_from_result = Mock(side_effect=Exception("Mock error"))

        verification_result = {
            "model_hash_changed": True,
            "repo_id": "test/model"
        }
        approved_files = ["test.py"]

        # Test function
        result = verify.save_verification_results(verification_result, approved_files)

        self.assertTrue(result.startswith("❌ Error saving verification results:"))
        self.assertIn("Mock error", result)

    @patch('model_sentinel.verify.verify.datetime')
    def test_update_approved_files_directory(self, mock_datetime):
        """Test _update_approved_files_directory function."""
        # Setup mock datetime
        mock_now = Mock()
        mock_now.isoformat.return_value = "2025-08-05T12:00:00Z"
        mock_datetime.now.return_value = mock_now

        verify = Verify()
        mock_model_dir = Mock()

        # Mock metadata operations
        initial_metadata = {
            "model_hash": "old_hash",
            "last_verified": "2025-08-04T12:00:00Z",
            "files": {}
        }
        verify.directory_manager.load_metadata = Mock(return_value=initial_metadata)
        verify.directory_manager.save_metadata = Mock()
        verify.directory_manager.save_file_content = Mock()

        verification_result = {
            "files_info": [
                {
                    "filename": "approved.py",
                    "hash": "hash1",
                    "content": "# Approved content"
                },
                {
                    "filename": "not_approved.py",
                    "hash": "hash2",
                    "content": "# Not approved content"
                }
            ]
        }
        approved_files = ["approved.py"]

        # Test function
        result = verify._update_approved_files_directory(
            mock_model_dir, verification_result, approved_files
        )

        # Assertions
        self.assertEqual(result, 1)

        # Check file content was saved
        verify.directory_manager.save_file_content.assert_called_once_with(
            mock_model_dir, "approved.py", "# Approved content"
        )

        # Check metadata was loaded and saved
        verify.directory_manager.load_metadata.assert_called_once_with(mock_model_dir)
        verify.directory_manager.save_metadata.assert_called_once()

        # Check metadata structure
        call_args, _ = verify.directory_manager.save_metadata.call_args
        saved_metadata = call_args[1]  # Second argument is the metadata
        expected_metadata = {
            "model_hash": "old_hash",
            "last_verified": "2025-08-05T12:00:00Z",
            "files": {
                "approved.py": {
                    "hash": "hash1",
                    "size": len("# Approved content".encode('utf-8')),
                    "verified_at": "2025-08-05T12:00:00Z"
                }
            }
        }
        self.assertEqual(saved_metadata, expected_metadata)


if __name__ == '__main__':
    unittest.main()
