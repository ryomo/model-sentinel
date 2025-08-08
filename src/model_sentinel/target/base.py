import hashlib
from pathlib import Path

from model_sentinel.verify.verify import Verify
from model_sentinel.verify.storage import StorageManager

VERIFICATION_FAILED_MESSAGE = "Model verification failed. Exiting for security reasons."


class TargetBase:
    """
    Base class for all target implementations.
    """

    def __init__(self):
        self.verify = Verify()
        self.storage = StorageManager()

    def _calculate_file_hash(self, file_path: Path | str) -> str:
        """
        Calculate SHA256 hash for a file.

        Args:
            file_path: Path to the file

        Returns:
            str: Hexadecimal hash of the file contents
        """
        hash_obj = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def _get_files_by_pattern(
        self, directory: Path | str, pattern: str = "*.py"
    ) -> list[Path]:
        """
        Get list of files in directory matching the pattern.

        Args:
            directory: Directory path to search
            pattern: Glob pattern to match files

        Returns:
            list[Path]: List of matching file paths
        """
        directory_path = Path(directory)
        return list(directory_path.rglob(pattern))

    def _calculate_directory_hash(
        self, directory: Path | str, pattern: str = "*.py"
    ) -> str:
        """
        Calculate hash for all files in directory matching the pattern.

        Args:
            directory: Directory path to hash
            pattern: Glob pattern to match files

        Returns:
            str: Hexadecimal hash of the directory contents
        """
        hash_obj = hashlib.sha256()
        directory_path = Path(directory)

        for file_path in sorted(directory_path.rglob(pattern)):
            # Add relative path to hash for consistency
            rel_path = file_path.relative_to(directory_path)
            hash_obj.update(str(rel_path).encode())

            # Add file content to hash
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    hash_obj.update(chunk)

        return hash_obj.hexdigest()

    def _read_file_content(self, file_path: Path | str) -> str:
        """
        Read file content as text.

        Args:
            file_path: Path to the file

        Returns:
            str: File content
        """
        return Path(file_path).read_text(encoding="utf-8")

    def _verify_files_workflow(
        self, files_to_check: list[dict], model_dir: Path
    ) -> bool:
        """
        Common workflow for verifying multiple files using directory system.

        Args:
            files_to_check: List of dicts with 'path', 'filename', 'hash', 'content'
            model_dir: Model directory

        Returns:
            bool: True if all files verified successfully
        """
        # Ensure storage directories exist
        self.storage.ensure_directories()

        all_verified = True
        session: list[dict] = []

        for file_info in files_to_check:
            filename = file_info["filename"]
            file_hash = file_info["hash"]
            content = file_info["content"]

            print(f"File: {filename}, Hash: {file_hash}")

            if not self.verify.check_file_changed(model_dir, filename, file_hash):
                # Not changed in storage; skip session record
                continue

            file_verified = self.verify.verify_file(filename, file_hash, content, model_dir)
            session.append(
                {
                    "filename": filename,
                    "hash": file_hash,
                    "content": content,
                    "approved": bool(file_verified),
                }
            )
            if not file_verified:
                all_verified = False

        # Always write run metadata (even if not all verified)
        try:
            self.verify.save_run_metadata(model_dir, session)
        except Exception as e:
            # Do not fail verification due to metadata write
            print(f"Warning: failed to write run metadata: {e}")

        return all_verified

    def get_model_directory_path(self, model_key: str, model_path: Path = None) -> Path:
        """
        Get directory path for model based on type.

        Args:
            model_key: Model key (e.g., "local/bert_a1b2c3d4" or "hf/microsoft/DialoGPT-medium@main")
            model_path: Original model path (for local models)

        Returns:
            Path to model directory
        """
        model_type, model_id = model_key.split('/', 1)

        if model_type == "local":
            if model_path:
                # Generate directory name and create if needed
                model_dir = self.storage.get_local_model_dir(model_path)
                # Save original path
                self.storage.save_original_path(model_dir, str(model_path))
                return model_dir
            else:
                # Use existing directory name
                return self.storage.local_dir / model_id
        elif model_type == "hf":
            if '@' in model_id:
                repo_id, revision = model_id.rsplit('@', 1)
            else:
                repo_id, revision = model_id, 'main'
            return self.storage.get_hf_model_dir(repo_id, revision)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def check_model_hash_changed(self, model_dir: Path, current_hash: str) -> bool:
        """
        Check if model hash has changed using directory system.

        Args:
            model_dir: Model directory
            current_hash: Current hash to compare

        Returns:
            bool: True if hash changed or is new, False if unchanged
        """
        metadata = self.storage.load_metadata(model_dir)
        previous_hash = metadata.get("model_hash")

        if previous_hash == current_hash:
            print("No changes detected in the model.")
            return False

        if previous_hash is None:
            print("No previous hash found. This is the first check.")
        else:
            print("Changes detected!")
            print(f"Previous hash: {previous_hash}")
            print(f"Current hash:  {current_hash}")

        return True

    def update_model_hash(self, model_dir: Path, new_hash: str):
        """Update model hash using directory system."""
        self.verify.update_model_hash(model_dir, new_hash)

    def register_model_in_registry(self, model_type: str, model_id: str, original_path: str = None):
        """Register model in the global registry."""
        kwargs = {}
        if original_path:
            kwargs["original_path"] = original_path
        self.storage.register_model(model_type, model_id, **kwargs)

    def handle_gui_verification(self, repo_id: str = None, revision: str = None, model_dir: str = None) -> bool:
        """Handle GUI-based verification."""
        try:
            from model_sentinel.gui.main import launch_verification_gui

            print("Changes detected. Launching GUI for verification...")
            return launch_verification_gui(repo_id=repo_id, revision=revision, model_dir=model_dir)
        except ImportError:
            print("GUI functionality requires gradio. Install with:")
            print("pip install 'model-sentinel[gui]'")
            return False
