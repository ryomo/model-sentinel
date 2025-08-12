import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from model_sentinel.verify.verify import Verify
from model_sentinel.verify.session import build_session_files
from model_sentinel.verify.storage import StorageManager


class TestMetadataBehavior(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base_dir = Path(self.tmp.name) / ".model-sentinel"
        self.storage = StorageManager(base_dir=self.base_dir)
        self.verify = Verify()
        # Inject test storage to avoid polluting project root
        self.verify.storage = self.storage

    def _model_dir(self) -> Path:
        # Create a predictable model dir for tests
        return self.storage.get_hf_model_dir("org/model", "main")

    def test_zero_approval_creates_run_and_none_overall(self):
        model_dir = self._model_dir()
        # Prepare verification_result with 2 files, none approved
        files_info = [
            {"filename": "README.md", "hash": "h1", "content": "A"},
            {"filename": "config.json", "hash": "h2", "content": "B"},
        ]
        session = build_session_files(files_info, approved_files=[])
        self.verify.save_run_metadata(model_dir, session)
        meta = self.storage.load_metadata(model_dir)
        self.assertEqual(meta.get("overall_status"), "ng")  # none approved -> ng
        self.assertIsInstance(meta.get("approved_files"), list)

    def test_mixed_approval_yields_mixed_overall(self):
        model_dir = self._model_dir()
        files_info = [
            {"filename": "a.txt", "hash": "h1", "content": "A"},
            {"filename": "b.txt", "hash": "h2", "content": "B"},
            {"filename": "c.txt", "hash": "h3", "content": "C"},
        ]
        session = build_session_files(files_info, approved_files=["a.txt", "b.txt"])
        self.verify.save_run_metadata(model_dir, session)
        meta = self.storage.load_metadata(model_dir)
        self.assertEqual(meta.get("overall_status"), "ng")
        self.assertTrue(any(it.get("path") == "a.txt" for it in meta.get("approved_files", [])))
        self.assertTrue(any(it.get("path") == "b.txt" for it in meta.get("approved_files", [])))

    def test_zero_file_session_sets_none_overall(self):
        model_dir = self._model_dir()
        session = []  # zero candidates
        self.verify.save_run_metadata(model_dir, session)
        meta = self.storage.load_metadata(model_dir)
        self.assertEqual(meta.get("overall_status"), "ok")


if __name__ == "__main__":
    unittest.main()
