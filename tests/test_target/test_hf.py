"""
Tests for model_sentinel.target.hf module.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path

from model_sentinel.target.hf import TargetHF, verify_hf_model


class TestTargetHF(unittest.TestCase):
    """Test cases for TargetHF class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.target = TargetHF()
        self.test_repo_id = "test/repo"
        self.test_revision = "main"
        self.test_model_hash = "abc123456"

    def test_init(self):
        """Test TargetHF class initialization."""
        target = TargetHF()
        self.assertIsNotNone(target.verify)

    def test_get_repo_key_with_revision(self):
        """Test repository key generation with revision."""
        result = self.target._get_repo_key("test/repo", "main")
        self.assertEqual(result, "hf/test/repo@main")

    def test_get_repo_key_without_revision(self):
        """Test repository key generation without revision."""
        result = self.target._get_repo_key("test/repo")
        self.assertEqual(result, "hf/test/repo")

    @patch('model_sentinel.target.hf.HfApi')
    def test_detect_model_changes_no_changes(self, mock_hf_api):
        """Test detect_model_changes when no changes are detected."""
        # Mock HfApi and model info
        mock_api = Mock()
        mock_hf_api.return_value = mock_api

        mock_model_info = Mock()
        mock_model_info.sha = "existing_hash"
        mock_api.model_info.return_value = mock_model_info

        with patch('model_sentinel.target.base.TargetBase.check_model_hash_changed', return_value=False):
            with patch('builtins.print'):
                result = self.target.detect_model_changes(self.test_repo_id, self.test_revision)

        self.assertIsNone(result)
        mock_api.model_info.assert_called_once_with(repo_id=self.test_repo_id, revision=self.test_revision)

    @patch('model_sentinel.target.hf.HfApi')
    def test_detect_model_changes_with_changes(self, mock_hf_api):
        """Test detect_model_changes when changes are detected."""
        # Mock HfApi and model info
        mock_api = Mock()
        mock_hf_api.return_value = mock_api

        mock_model_info = Mock()
        mock_model_info.sha = "new_hash"
        mock_api.model_info.return_value = mock_model_info

        with patch('model_sentinel.target.base.TargetBase.check_model_hash_changed', return_value=True):
            with patch('builtins.print'):
                result = self.target.detect_model_changes(self.test_repo_id, self.test_revision)

        self.assertEqual(result, "new_hash")

    def test_update_model_hash_for_repo(self):
        """Test updating model hash for repository."""
        # Create test model directory using directory system
        model_dir = self.target.directory_manager.get_hf_model_dir(self.test_repo_id, self.test_revision)
        model_dir.mkdir(parents=True, exist_ok=True)

        # Set initial metadata
        initial_metadata = {
            "model_hash": "old_hash",
            "last_verified": "2025-07-27T00:00:00Z",
            "files": {}
        }
        self.target.directory_manager.save_metadata(model_dir, initial_metadata)

        # Update model hash
        self.target.update_model_hash_for_repo(self.test_repo_id, self.test_revision, "new_hash")

        # Verify the data was updated
        updated_metadata = self.target.directory_manager.load_metadata(model_dir)
        self.assertEqual(updated_metadata["model_hash"], "new_hash")

    @patch('model_sentinel.target.hf.HfApi')
    def test_verify_remote_files_success(self, mock_hf_api):
        """Test verify_remote_files when verification is successful."""
        # Mock HfApi and model info
        mock_api = Mock()
        mock_hf_api.return_value = mock_api

        # Mock sibling file
        mock_sibling = Mock()
        mock_sibling.rfilename = "test.py"
        mock_sibling.blob_id = "file_hash_123"

        mock_model_info = Mock()
        mock_model_info.siblings = [mock_sibling]
        mock_api.model_info.return_value = mock_model_info

        # Mock file download
        with patch.object(self.target, '_download_file_content', return_value="print('test')"):
            with patch.object(self.target, '_verify_files_workflow', return_value=True):
                with patch('builtins.print'):
                    result = self.target.verify_remote_files(self.test_repo_id, self.test_revision)

        self.assertTrue(result)

    @patch('model_sentinel.target.hf.HfApi')
    def test_verify_remote_files_download_failure(self, mock_hf_api):
        """Test verify_remote_files when file download fails."""
        # Mock HfApi and model info
        mock_api = Mock()
        mock_hf_api.return_value = mock_api

        # Mock sibling file
        mock_sibling = Mock()
        mock_sibling.rfilename = "test.py"
        mock_sibling.blob_id = "file_hash_123"

        mock_model_info = Mock()
        mock_model_info.siblings = [mock_sibling]
        mock_api.model_info.return_value = mock_model_info

        # Mock file download failure
        with patch.object(self.target, '_download_file_content', return_value=None):
            with patch('builtins.print'):
                result = self.target.verify_remote_files(self.test_repo_id, self.test_revision)

        self.assertFalse(result)

    @patch('model_sentinel.target.hf.HfApi')
    def test_download_file_content_success(self, mock_hf_api):
        """Test successful file download."""
        mock_api = Mock()
        mock_hf_api.return_value = mock_api

        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as temp_file:
            temp_file.write("print('hello world')")
            temp_file_path = temp_file.name

        try:
            mock_api.hf_hub_download.return_value = temp_file_path

            with patch('builtins.print'):
                result = self.target._download_file_content(mock_api, self.test_repo_id, self.test_revision, "test.py")

            self.assertEqual(result, "print('hello world')")
            mock_api.hf_hub_download.assert_called_once_with(
                repo_id=self.test_repo_id,
                filename="test.py",
                revision=self.test_revision
            )
        finally:
            # Clean up temporary file
            Path(temp_file_path).unlink()

    @patch('model_sentinel.target.hf.HfApi')
    def test_download_file_content_failure(self, mock_hf_api):
        """Test file download failure."""
        mock_api = Mock()
        mock_hf_api.return_value = mock_api

        # Mock download exception
        mock_api.hf_hub_download.side_effect = Exception("Network error")

        with patch('builtins.print'):
            result = self.target._download_file_content(mock_api, self.test_repo_id, self.test_revision, "test.py")

        self.assertIsNone(result)

    @patch('model_sentinel.target.hf.HfApi')
    def test_get_files_for_verification_success(self, mock_hf_api):
        """Test get_files_for_verification with successful file retrieval."""
        mock_api = Mock()
        mock_hf_api.return_value = mock_api

        # Mock sibling files
        mock_sibling1 = Mock()
        mock_sibling1.rfilename = "test1.py"
        mock_sibling1.blob_id = "hash1"

        mock_sibling2 = Mock()
        mock_sibling2.rfilename = "test2.txt"  # Non-Python file
        mock_sibling2.blob_id = "hash2"

        mock_model_info = Mock()
        mock_model_info.siblings = [mock_sibling1, mock_sibling2]
        mock_api.model_info.return_value = mock_model_info

        # Mock file download for Python files only
        def mock_download_side_effect(api, repo_id, revision, filename):
            if filename.endswith('.py'):
                return f"# Content of {filename}"
            return None

        with patch.object(self.target, '_download_file_content', side_effect=mock_download_side_effect):
            result = self.target.get_files_for_verification(self.test_repo_id, self.test_revision)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['filename'], 'test1.py')
        self.assertEqual(result[0]['content'], '# Content of test1.py')
        self.assertEqual(result[0]['hash'], 'hash1')

    @patch('model_sentinel.target.hf.HfApi')
    def test_get_files_for_verification_exception(self, mock_hf_api):
        """Test get_files_for_verification when exception occurs."""
        mock_api = Mock()
        mock_hf_api.return_value = mock_api

        # Mock API exception
        mock_api.model_info.side_effect = Exception("API error")

        with patch('builtins.print'):
            result = self.target.get_files_for_verification(self.test_repo_id, self.test_revision)

        self.assertEqual(result, [])


class TestVerifyHFModel(unittest.TestCase):
    """Test cases for verify_hf_model function."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_repo_id = "test/repo"
        self.test_revision = "main"

    @patch('model_sentinel.target.hf.TargetHF')
    def test_verify_hf_model_no_changes(self, mock_target_class):
        """Test verify_hf_model when no changes are detected."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = None

        with patch('builtins.print'):
            result = verify_hf_model(self.test_repo_id, self.test_revision)

        self.assertTrue(result)
        mock_target.detect_model_changes.assert_called_once_with(self.test_repo_id, revision=self.test_revision)

    @patch('model_sentinel.target.hf.TargetHF')
    def test_verify_hf_model_cli_success(self, mock_target_class):
        """Test verify_hf_model CLI mode with successful verification."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.verify_remote_files.return_value = True

        with patch('builtins.print'):
            result = verify_hf_model(self.test_repo_id, self.test_revision, gui=False)

        self.assertTrue(result)
        mock_target.verify_remote_files.assert_called_once_with(self.test_repo_id, revision=self.test_revision)
        mock_target.update_model_hash_for_repo.assert_called_once_with(self.test_repo_id, self.test_revision, "new_hash")

    @patch('model_sentinel.target.hf.TargetHF')
    def test_verify_hf_model_cli_failure_no_exit(self, mock_target_class):
        """Test verify_hf_model CLI mode with verification failure and no exit."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.verify_remote_files.return_value = False

        with patch('builtins.print'):
            result = verify_hf_model(self.test_repo_id, self.test_revision, gui=False, exit_on_reject=False)

        self.assertFalse(result)

    @patch('model_sentinel.target.hf.TargetHF')
    def test_verify_hf_model_gui_import_error(self, mock_target_class):
        """Test verify_hf_model GUI mode when gradio is not available."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.handle_gui_verification.return_value = False

        with patch('builtins.print'):
            result = verify_hf_model(self.test_repo_id, self.test_revision, gui=True, exit_on_reject=False)

        mock_target.handle_gui_verification.assert_called_once_with(repo_id=self.test_repo_id, revision=self.test_revision)
        self.assertFalse(result)

    @patch('model_sentinel.target.hf.TargetHF')
    def test_verify_hf_model_gui_closed_with_exit_on_reject_true(self, mock_target_class):
        """Test verify_hf_model GUI mode when GUI is closed with exit_on_reject=True."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.handle_gui_verification.return_value = False

        with patch('builtins.print'):
            with patch('builtins.exit') as mock_exit:
                result = verify_hf_model(self.test_repo_id, revision=self.test_revision, gui=True, exit_on_reject=True)

        # Verify GUI handler was called
        mock_target.handle_gui_verification.assert_called_once_with(repo_id=self.test_repo_id, revision=self.test_revision)

        # exit() should be called when exit_on_reject=True and verification fails
        mock_exit.assert_called_once_with(1)
        self.assertFalse(result)

    @patch('model_sentinel.target.hf.TargetHF')
    def test_verify_hf_model_gui_closed_with_exit_on_reject_false(self, mock_target_class):
        """Test verify_hf_model GUI mode when GUI is closed with exit_on_reject=False."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.handle_gui_verification.return_value = False

        with patch('builtins.print'):
            with patch('builtins.exit') as mock_exit:
                result = verify_hf_model(self.test_repo_id, self.test_revision, gui=True, exit_on_reject=False)

        # Verify GUI handler was called
        mock_target.handle_gui_verification.assert_called_once_with(repo_id=self.test_repo_id, revision=self.test_revision)

        # exit() should NOT be called when exit_on_reject=False
        mock_exit.assert_not_called()
        self.assertFalse(result)

    @patch('model_sentinel.target.hf.TargetHF')
    def test_verify_hf_model_gui_success(self, mock_target_class):
        """Test verify_hf_model GUI mode with successful verification."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.handle_gui_verification.return_value = True

        with patch('builtins.print'):
            result = verify_hf_model(self.test_repo_id, self.test_revision, gui=True, exit_on_reject=False)

        # Verify GUI handler was called
        mock_target.handle_gui_verification.assert_called_once_with(repo_id=self.test_repo_id, revision=self.test_revision)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
