"""Test cases for model_sentinel.target.local module."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile
import tempfile
from unittest.mock import Mock, patch

from model_sentinel.target.local import TargetLocal, verify_local_model


class TestTargetLocal(unittest.TestCase):
    """Test cases for TargetLocal class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.target = TargetLocal()
        self.test_model_dir = Path("/tmp/test_model")
        # Route storage to temp dir
        self._temp_dir = Path(tempfile.mkdtemp())
        self.target.storage = self.target.storage.__class__(self._temp_dir / ".model-sentinel")

    def tearDown(self):
        # Cleanup temp storage
        if hasattr(self, "_temp_dir") and self._temp_dir.exists():
            for p in sorted(self._temp_dir.rglob("*"), reverse=True):
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    try:
                        p.rmdir()
                    except Exception:
                        pass
            try:
                self._temp_dir.rmdir()
            except Exception:
                pass

    def test_init(self):
        """Test TargetLocal class initialization."""
        target = TargetLocal()
        self.assertIsInstance(target, TargetLocal)
        self.assertIsNotNone(target.verify)

    def test_get_model_key(self):
        """Test model key generation."""
        result = self.target._get_model_key(self.test_model_dir)
        # The model key should start with "local/" followed by the directory name and hash
        self.assertTrue(result.startswith("local/"))
        self.assertIn("model", result)  # Directory name should be included

    def test_detect_model_changes_no_changes(self):
        """Test detect_model_changes when no changes are detected."""
        test_hash = "test_hash_123"

        with patch.object(self.target, '_calculate_directory_hash', return_value=test_hash):
            with patch('model_sentinel.target.base.TargetBase.check_model_hash_changed', return_value=False):
                with patch('builtins.print'):
                    result = self.target.detect_model_changes(self.test_model_dir)

        self.assertIsNone(result)

    def test_detect_model_changes_with_changes(self):
        """Test detect_model_changes when changes are detected."""
        new_hash = "new_hash_456"

        with patch.object(self.target, '_calculate_directory_hash', return_value=new_hash):
            with patch('model_sentinel.target.base.TargetBase.check_model_hash_changed', return_value=True):
                with patch('builtins.print'):
                    result = self.target.detect_model_changes(self.test_model_dir)

        self.assertEqual(result, new_hash)

    def test_detect_model_changes_new_model(self):
        """Test detect_model_changes for a new model (no existing data)."""
        new_hash = "new_hash_123"

        with patch.object(self.target, '_calculate_directory_hash', return_value=new_hash):
            with patch('model_sentinel.target.base.TargetBase.check_model_hash_changed', return_value=True):
                with patch('builtins.print'):
                    result = self.target.detect_model_changes(self.test_model_dir)

        self.assertEqual(result, new_hash)

    def test_verify_local_files_success(self):
        """Test verify_local_files when verification is successful."""
        # Create temporary test files
        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            # Create test Python files
            test_file1 = temp_model_dir / "test1.py"
            test_file2 = temp_model_dir / "test2.py"
            test_file1.write_text("print('test1')")
            test_file2.write_text("print('test2')")

            with patch.object(self.target, '_verify_files_workflow', return_value=True):
                with patch('builtins.print'):
                    result = self.target.verify_local_files(temp_model_dir)

            self.assertTrue(result)

    def test_verify_local_files_failure(self):
        """Test verify_local_files when verification fails."""
        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            # Create test Python file
            test_file = temp_model_dir / "test.py"
            test_file.write_text("print('test')")

            with patch.object(self.target, '_verify_files_workflow', return_value=False):
                with patch('builtins.print'):
                    result = self.target.verify_local_files(temp_model_dir)

            self.assertFalse(result)

    def test_get_files_for_verification(self):
        """Test get_files_for_verification returns file information."""
        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            # Create test Python file
            test_file = temp_model_dir / "test.py"
            test_content = "print('hello world')"
            test_file.write_text(test_content)

            result = self.target.get_files_for_verification(temp_model_dir)

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["filename"], "test.py")
            self.assertEqual(result[0]["content"], test_content)
            self.assertIn("hash", result[0])
            self.assertIn("path", result[0])

    def test_get_files_for_verification_multiple_files(self):
        """Test get_files_for_verification with multiple Python files."""
        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            # Create multiple test Python files
            files_data = {
                "file1.py": "def func1(): pass",
                "subdir/file2.py": "def func2(): pass",
                "file3.py": "class TestClass: pass"
            }

            for file_path, content in files_data.items():
                full_path = temp_model_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)

            result = self.target.get_files_for_verification(temp_model_dir)

            self.assertEqual(len(result), 3)
            filenames = [file_info["filename"] for file_info in result]
            self.assertIn("file1.py", filenames)
            self.assertIn("subdir/file2.py", filenames)
            self.assertIn("file3.py", filenames)

    def test_get_files_for_verification_no_python_files(self):
        """Test get_files_for_verification when no Python files exist."""
        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            # Create non-Python files
            (temp_model_dir / "readme.txt").write_text("readme")
            (temp_model_dir / "config.json").write_text('{"key": "value"}')

            result = self.target.get_files_for_verification(temp_model_dir)

            self.assertEqual(len(result), 0)


class TestVerifyLocalModel(unittest.TestCase):
    """Test cases for verify_local_model function."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_model_dir = Path("/tmp/test_model")

    def test_verify_local_model_directory_not_exists(self):
        """Test verify_local_model when model directory doesn't exist."""
        non_existent_dir = Path("/non/existent/directory")

        with patch('builtins.print'):
            result = verify_local_model(non_existent_dir, exit_on_reject=False)

        self.assertFalse(result)

    @patch('model_sentinel.target.local.TargetLocal')
    def test_verify_local_model_no_changes(self, mock_target_class):
        """Test verify_local_model when no changes are detected."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = None

        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            with patch('builtins.print'):
                result = verify_local_model(temp_model_dir)

        self.assertTrue(result)
        mock_target.detect_model_changes.assert_called_once_with(temp_model_dir)

    @patch('model_sentinel.target.local.TargetLocal')
    def test_verify_local_model_cli_success(self, mock_target_class):
        """Test verify_local_model CLI mode with successful verification."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.verify_local_files.return_value = True
        mock_target._get_model_key.return_value = "local/test/path"

        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            with patch('builtins.print'):
                result = verify_local_model(temp_model_dir, gui=False)

        self.assertTrue(result)
        mock_target.verify_local_files.assert_called_once_with(temp_model_dir)
        mock_target.update_model_hash.assert_called_once()

    @patch('model_sentinel.target.local.TargetLocal')
    def test_verify_local_model_cli_failure_no_exit(self, mock_target_class):
        """Test verify_local_model CLI mode with verification failure and no exit."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.verify_local_files.return_value = False

        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            with patch('builtins.print'):
                result = verify_local_model(temp_model_dir, gui=False, exit_on_reject=False)

        self.assertFalse(result)
        mock_target.verify_local_files.assert_called_once_with(temp_model_dir)

    @patch('model_sentinel.target.local.TargetLocal')
    def test_verify_local_model_gui_success(self, mock_target_class):
        """Test verify_local_model GUI mode with successful verification."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.handle_gui_verification.return_value = True

        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            with patch('builtins.print'):
                result = verify_local_model(temp_model_dir, gui=True)

        self.assertTrue(result)
        mock_target.handle_gui_verification.assert_called_once_with(model_dir=temp_model_dir)

    @patch('model_sentinel.target.local.TargetLocal')
    def test_verify_local_model_gui_import_error(self, mock_target_class):
        """Test verify_local_model GUI mode when gradio is not available."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.handle_gui_verification.return_value = False

        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            with patch('builtins.print'):
                result = verify_local_model(temp_model_dir, gui=True, exit_on_reject=False)

        mock_target.handle_gui_verification.assert_called_once_with(model_dir=temp_model_dir)
        self.assertFalse(result)

    @patch('model_sentinel.target.local.TargetLocal')
    def test_verify_local_model_gui_closed_with_exit_on_reject_true(self, mock_target_class):
        """Test verify_local_model GUI mode when GUI is closed with exit_on_reject=True."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.handle_gui_verification.return_value = False

        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            with patch('builtins.print'):
                with patch('builtins.exit') as mock_exit:
                    result = verify_local_model(temp_model_dir, gui=True, exit_on_reject=True)

        # Verify GUI handler was called
        mock_target.handle_gui_verification.assert_called_once_with(model_dir=temp_model_dir)

        # exit() should be called when exit_on_reject=True and verification fails
        mock_exit.assert_called_once_with(1)
        self.assertFalse(result)

    @patch('model_sentinel.target.local.TargetLocal')
    def test_verify_local_model_gui_closed_with_exit_on_reject_false(self, mock_target_class):
        """Test verify_local_model GUI mode when GUI is closed with exit_on_reject=False."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = "new_hash"
        mock_target.handle_gui_verification.return_value = False

        with TemporaryDirectory() as temp_dir:
            temp_model_dir = Path(temp_dir)

            with patch('builtins.print'):
                with patch('builtins.exit') as mock_exit:
                    result = verify_local_model(temp_model_dir, gui=True, exit_on_reject=False)

        # Verify GUI handler was called
        mock_target.handle_gui_verification.assert_called_once_with(model_dir=temp_model_dir)

        # exit() should NOT be called when exit_on_reject=False
        mock_exit.assert_not_called()
        self.assertFalse(result)

    @patch('model_sentinel.target.local.TargetLocal')
    def test_verify_local_model_with_string_path(self, mock_target_class):
        """Test verify_local_model with string path parameter."""
        mock_target = Mock()
        mock_target_class.return_value = mock_target
        mock_target.detect_model_changes.return_value = None

        with TemporaryDirectory() as temp_dir:
            with patch('builtins.print'):
                result = verify_local_model(str(temp_dir))

        self.assertTrue(result)
        # Verify that the string path was converted to Path object
        mock_target.detect_model_changes.assert_called_once_with(Path(temp_dir))


if __name__ == '__main__':
    unittest.main()
