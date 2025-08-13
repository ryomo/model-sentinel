import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from model_sentinel.verify.storage import StorageManager


class TestStorageManagerLocalDirName(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        # Create a fake local model directory
        self.model_dir = self.tmpdir / "model"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        # Add initial python files
        (self.model_dir / "a.py").write_text("print('A')\n", encoding="utf-8")
        sub = self.model_dir / "pkg"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / "b.py").write_text("print('B')\n", encoding="utf-8")

        self.storage = StorageManager(base_dir=self.tmpdir / ".model-sentinel")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_dir_name_uses_content_hash8(self):
        name = self.storage.generate_local_model_dir_name(self.model_dir)
        # Prefix should be model directory name
        self.assertTrue(name.startswith("model_"))
        # Suffix should be 8 hex chars
        suffix = name.split("_", 1)[1]
        self.assertRegex(suffix, r"^[0-9a-f]{8}$")

    def test_hash_changes_on_content_change(self):
        name1 = self.storage.generate_local_model_dir_name(self.model_dir)
        # Modify one file content
        (self.model_dir / "a.py").write_text("print('A2')\n", encoding="utf-8")
        name2 = self.storage.generate_local_model_dir_name(self.model_dir)
        self.assertNotEqual(name1, name2)

    def test_hash_changes_when_python_file_added(self):
        name1 = self.storage.generate_local_model_dir_name(self.model_dir)
        # Add new *.py file (should affect hash)
        (self.model_dir / "new_added.py").write_text("x=1\n", encoding="utf-8")
        name2 = self.storage.generate_local_model_dir_name(self.model_dir)
        self.assertNotEqual(name1, name2)

    def test_empty_directory_hash_is_stable(self):
        empty_dir = self.tmpdir / "empty"
        empty_dir.mkdir()
        # No *.py files; content hash should equal sha256("")'s hexdigest
        name = self.storage.generate_local_model_dir_name(empty_dir)
        suffix = name.split("_", 1)[1]
        expected_hash8 = hashlib.sha256(b"").hexdigest()[:8]
        self.assertEqual(suffix, expected_hash8)
