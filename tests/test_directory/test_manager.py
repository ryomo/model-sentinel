"""Tests for directory manager functionality."""

import unittest
from pathlib import Path
import tempfile
import shutil
import json
from datetime import datetime

from model_sentinel.directory.manager import DirectoryManager


class TestDirectoryManager(unittest.TestCase):
    """Test directory manager functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.directory_manager = DirectoryManager(self.temp_dir / ".model-sentinel")

    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_ensure_directories(self):
        """Test directory creation."""
        self.directory_manager.ensure_directories()

        self.assertTrue(self.directory_manager.base_dir.exists())
        self.assertTrue(self.directory_manager.hf_dir.exists())
        self.assertTrue(self.directory_manager.local_dir.exists())

    def test_generate_local_model_dir_name(self):
        """Test local model directory name generation."""
        model_path = Path("/home/user/models/bert")
        dir_name = self.directory_manager.generate_local_model_dir_name(model_path)

        # Should be in format: bert_{hash}
        self.assertTrue(dir_name.startswith("bert_"))
        self.assertEqual(len(dir_name), 13)  # "bert_" + 8 character hash

    def test_get_local_model_dir(self):
        """Test getting local model directory path."""
        model_path = Path("/home/user/models/bert")
        model_dir = self.directory_manager.get_local_model_dir(model_path)

        expected_name = self.directory_manager.generate_local_model_dir_name(model_path)
        expected_path = self.directory_manager.local_dir / expected_name

        self.assertEqual(model_dir, expected_path)

    def test_get_hf_model_dir(self):
        """Test getting HF model directory path."""
        repo_id = "microsoft/DialoGPT-medium"
        revision = "main"
        model_dir = self.directory_manager.get_hf_model_dir(repo_id, revision)

        expected_path = self.directory_manager.hf_dir / "microsoft" / "DialoGPT-medium@main"
        self.assertEqual(model_dir, expected_path)

    def test_registry_operations(self):
        """Test registry loading and saving."""
        # Load empty registry
        registry = self.directory_manager.load_registry()
        self.assertEqual(registry, {"models": {}})

        # Add model and save
        registry["models"]["test/model"] = {
            "type": "test",
            "last_verified": datetime.now().isoformat()
        }
        self.directory_manager.save_registry(registry)

        # Load and verify
        loaded_registry = self.directory_manager.load_registry()
        self.assertIn("test/model", loaded_registry["models"])

    def test_metadata_operations(self):
        """Test metadata loading and saving."""
        model_dir = self.temp_dir / "test_model"

        # Load non-existent metadata
        metadata = self.directory_manager.load_metadata(model_dir)
        expected = {
            "model_hash": None,
            "last_verified": None,
            "files": {}
        }
        self.assertEqual(metadata, expected)

        # Save and load metadata
        test_metadata = {
            "model_hash": "test_hash",
            "last_verified": datetime.now().isoformat(),
            "files": {
                "test.py": {
                    "hash": "file_hash",
                    "size": 100
                }
            }
        }
        self.directory_manager.save_metadata(model_dir, test_metadata)

        loaded_metadata = self.directory_manager.load_metadata(model_dir)
        self.assertEqual(loaded_metadata["model_hash"], "test_hash")

    def test_file_content_operations(self):
        """Test file content saving and loading."""
        model_dir = self.temp_dir / "test_model"
        filename = "test.py"
        content = "print('Hello, World!')"

        # Save file content
        self.directory_manager.save_file_content(model_dir, filename, content)

        # Load and verify
        loaded_content = self.directory_manager.load_file_content(model_dir, filename)
        self.assertEqual(loaded_content, content)

        # Test non-existent file
        non_existent = self.directory_manager.load_file_content(model_dir, "non_existent.py")
        self.assertIsNone(non_existent)

    def test_original_path_operations(self):
        """Test original path saving and loading."""
        model_dir = self.temp_dir / "test_model"
        original_path = "/home/user/models/bert"

        # Save original path
        self.directory_manager.save_original_path(model_dir, original_path)

        # Load and verify
        loaded_path = self.directory_manager.load_original_path(model_dir)
        self.assertEqual(loaded_path, original_path)

        # Test non-existent path
        non_existent_dir = self.temp_dir / "non_existent"
        non_existent_path = self.directory_manager.load_original_path(non_existent_dir)
        self.assertIsNone(non_existent_path)

    def test_model_key_generation(self):
        """Test model key generation."""
        key1 = self.directory_manager.get_model_key("local", "bert_a1b2c3d4")
        self.assertEqual(key1, "local/bert_a1b2c3d4")

        key2 = self.directory_manager.get_model_key("hf", "microsoft/DialoGPT-medium@main")
        self.assertEqual(key2, "hf/microsoft/DialoGPT-medium@main")

    def test_register_model(self):
        """Test model registration."""
        self.directory_manager.register_model(
            "local",
            "bert_a1b2c3d4",
            original_path="/home/user/models/bert"
        )

        registry = self.directory_manager.load_registry()
        model_info = registry["models"]["local/bert_a1b2c3d4"]

        self.assertEqual(model_info["type"], "local")
        self.assertEqual(model_info["original_path"], "/home/user/models/bert")
        self.assertEqual(model_info["status"], "verified")
        self.assertIsNotNone(model_info["last_verified"])


if __name__ == "__main__":
    unittest.main()
