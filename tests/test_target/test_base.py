"""
Tests for model_sentinel.target.base module.
"""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from model_sentinel.target.base import TargetBase, VERIFICATION_FAILED_MESSAGE


class TestTargetBase(unittest.TestCase):
    """Test cases for TargetBase class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.target = TargetBase()
        self.temp_dir = Path(tempfile.mkdtemp())
        # Route storage to temp dir to avoid polluting repo
        self.target.storage = self.target.storage.__class__(self.temp_dir / ".model-sentinel")

        # Create test files
        self.test_py_file = self.temp_dir / "test.py"
        self.test_py_file.write_text("print('hello world')")

        self.test_txt_file = self.temp_dir / "test.txt"
        self.test_txt_file.write_text("test content")

        # Create subdirectory with another Python file
        self.sub_dir = self.temp_dir / "subdir"
        self.sub_dir.mkdir()
        self.sub_py_file = self.sub_dir / "sub.py"
        self.sub_py_file.write_text("def func(): pass")

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Clean up temporary files
        for file in self.temp_dir.rglob("*"):
            if file.is_file():
                file.unlink()
        for dir in sorted(self.temp_dir.rglob("*"), reverse=True):
            if dir.is_dir():
                dir.rmdir()
        self.temp_dir.rmdir()

    def test_init(self):
        """Test TargetBase class initialization."""
        target = TargetBase()
        self.assertIsNotNone(target.verify)

    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        expected_content = "print('hello world')"
        expected_hash = hashlib.sha256(expected_content.encode()).hexdigest()

        result_hash = self.target._calculate_file_hash(self.test_py_file)
        self.assertEqual(result_hash, expected_hash)

    def test_calculate_file_hash_with_string_path(self):
        """Test file hash calculation with string path."""
        expected_content = "print('hello world')"
        expected_hash = hashlib.sha256(expected_content.encode()).hexdigest()

        result_hash = self.target._calculate_file_hash(str(self.test_py_file))
        self.assertEqual(result_hash, expected_hash)

    def test_get_files_by_pattern_default(self):
        """Test getting files by default pattern (*.py)."""
        files = self.target._get_files_by_pattern(self.temp_dir)

        # Should find both Python files
        file_names = [f.name for f in files]
        self.assertIn("test.py", file_names)
        self.assertIn("sub.py", file_names)
        self.assertEqual(len(files), 2)

    def test_get_files_by_pattern_custom(self):
        """Test getting files by custom pattern."""
        files = self.target._get_files_by_pattern(self.temp_dir, "*.txt")

        # Should find only txt file
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "test.txt")

    def test_get_files_by_pattern_string_path(self):
        """Test getting files by pattern with string path."""
        files = self.target._get_files_by_pattern(str(self.temp_dir), "*.py")

        # Should find both Python files
        self.assertEqual(len(files), 2)

    def test_calculate_directory_hash(self):
        """Test directory hash calculation."""
        # Calculate hash manually for verification
        hash_obj = hashlib.sha256()

        # Files should be processed in sorted order
        py_files = sorted(self.temp_dir.rglob("*.py"))
        for file_path in py_files:
            rel_path = file_path.relative_to(self.temp_dir)
            hash_obj.update(str(rel_path).encode())
            hash_obj.update(file_path.read_bytes())

        expected_hash = hash_obj.hexdigest()
        result_hash = self.target._calculate_directory_hash(self.temp_dir)

        self.assertEqual(result_hash, expected_hash)

    def test_calculate_directory_hash_with_pattern(self):
        """Test directory hash calculation with custom pattern."""
        result_hash = self.target._calculate_directory_hash(self.temp_dir, "*.txt")

        # Should only include txt files
        hash_obj = hashlib.sha256()
        rel_path = self.test_txt_file.relative_to(self.temp_dir)
        hash_obj.update(str(rel_path).encode())
        hash_obj.update(self.test_txt_file.read_bytes())
        expected_hash = hash_obj.hexdigest()

        self.assertEqual(result_hash, expected_hash)

    def test_read_file_content(self):
        """Test reading file content."""
        content = self.target._read_file_content(self.test_py_file)
        self.assertEqual(content, "print('hello world')")

    def test_read_file_content_string_path(self):
        """Test reading file content with string path."""
        content = self.target._read_file_content(str(self.test_py_file))
        self.assertEqual(content, "print('hello world')")

    def test_verification_failed_message_constant(self):
        """Test that verification failed message constant is defined."""
        self.assertEqual(
            VERIFICATION_FAILED_MESSAGE,
            "Model verification failed. Exiting for security reasons."
        )

    def test_calculate_file_hash_nonexistent_file(self):
        """Test file hash calculation with nonexistent file."""
        nonexistent_file = self.temp_dir / "nonexistent.py"

        with self.assertRaises(FileNotFoundError):
            self.target._calculate_file_hash(nonexistent_file)

    def test_get_files_by_pattern_empty_directory(self):
        """Test getting files from empty directory."""
        empty_dir = self.temp_dir / "empty"
        empty_dir.mkdir()

        files = self.target._get_files_by_pattern(empty_dir)
        self.assertEqual(len(files), 0)

    def test_calculate_directory_hash_empty_directory(self):
        """Test directory hash calculation for empty directory."""
        empty_dir = self.temp_dir / "empty"
        empty_dir.mkdir()

        result_hash = self.target._calculate_directory_hash(empty_dir)

        # Empty directory should produce hash of empty string
        expected_hash = hashlib.sha256().hexdigest()
        self.assertEqual(result_hash, expected_hash)


if __name__ == '__main__':
    unittest.main()
