from pathlib import Path
import pydoc
from datetime import datetime
from typing import Dict, Any, Optional

from model_sentinel.storage.manager import StorageManager


class Verify:
    """Base class for verifying model changes and file integrity."""

    def __init__(self):
        # Storage system
        self.storage = StorageManager()

    def verify_file(self, filename: str, current_hash: str, content: str,
                   model_dir: Path) -> bool:
        """Verify file content and update storage if confirmed.

        Args:
            filename: Name of the file being verified
            current_hash: Current hash of the file
            content: File content
            model_dir: Model storage directory

        Returns:
            True if file is verified and storage updated, False otherwise.
        """
        if self.prompt_user_verification(filename, content):
            # Save file content
            self.storage.save_file_content(model_dir, filename, content)

            # Update metadata
            metadata = self.storage.load_metadata(model_dir)
            metadata["files"][filename] = {
                "hash": current_hash,
                "size": len(content.encode('utf-8')),
                "verified_at": datetime.now().isoformat()
            }
            metadata["last_verified"] = datetime.now().isoformat()
            self.storage.save_metadata(model_dir, metadata)

            print("Trust confirmed. File content and hash updated.")
            return True
        else:
            print("Trust not confirmed. Please review the file changes.")
            return False

    def update_model_hash(self, model_dir: Path, new_hash: str) -> None:
        """Update model hash in metadata.

        Args:
            model_dir: Model storage directory
            new_hash: New model hash
        """
        metadata = self.storage.load_metadata(model_dir)
        metadata["model_hash"] = new_hash
        metadata["last_verified"] = datetime.now().isoformat()
        self.storage.save_metadata(model_dir, metadata)
        print(f"Model hash updated to: {new_hash}")

    def check_file_changed(self, model_dir: Path, filename: str, current_hash: str) -> bool:
        """Check if file hash has changed in storage system.

        Args:
            model_dir: Model storage directory
            filename: Filename to check
            current_hash: Current file hash

        Returns:
            True if file changed or is new, False if unchanged
        """
        metadata = self.storage.load_metadata(model_dir)
        file_info = metadata.get("files", {}).get(filename)

        if file_info is None:
            print(f"No previous hash found for {filename}. This is the first check.")
            return True

        previous_hash = file_info.get("hash")
        if previous_hash == current_hash:
            print(f"No changes detected in {filename}.")
            return False

        print(f"Changes detected in {filename}!")
        return True

    def prompt_user_verification(self, item_name, content):
        """Prompt user for verification of changes."""
        pydoc.pager(
            f"{item_name} has been updated.\n"
            f"--- Content of {item_name} ---\n\n"
            + content
            + "\n\n--- End of content ---\n"
        )

        message = f"Do you trust {item_name}? (y/N): "
        response = input(message)
        return response.lower() in ["y", "yes"]

    def list_verified_hashes(self):
        """Display all verified models and hashes in a human-readable format."""
        # Load from storage system
        registry = self.storage.load_registry()
        models = registry.get("models", {})

        if not models:
            print("No verified models found.")
            return

        print("=== Verified Models Summary ===")
        for model_key, model_info in models.items():
            self._display_model_info(model_key, model_info)
            print("-" * 50)

    def _display_model_info(self, model_key: str, model_info: Dict[str, Any]) -> None:
        """Display information for a single model."""
        print(f"\nModel: {model_key}")
        print(f"Type: {model_info.get('type', 'unknown')}")
        print(f"Last Verified: {model_info.get('last_verified', 'unknown')}")
        print(f"Status: {model_info.get('status', 'unknown')}")

        if model_info.get('original_path'):
            print(f"Original Path: {model_info['original_path']}")

        # Get model directory
        model_dir = self._get_model_dir_from_info(model_key, model_info)
        if model_dir and model_dir.exists():
            self._display_file_info(model_dir)
        else:
            print("  Files: Metadata not found")

    def _get_model_dir_from_info(self, model_key: str, model_info: Dict[str, Any]) -> Optional[Path]:
        """Get model directory path from model info."""
        model_type = model_info.get('type')

        if model_type == 'local':
            model_id = model_key.split('/', 1)[1]
            return self.storage.local_dir / model_id
        elif model_type == 'hf':
            model_path = model_key.split('/', 1)[1]
            if '@' in model_path:
                repo_parts, revision = model_path.rsplit('@', 1)
            else:
                repo_parts, revision = model_path, 'main'
            return self.storage.get_hf_model_dir(repo_parts, revision)

        return None

    def _display_file_info(self, model_dir: Path) -> None:
        """Display file information for a model."""
        metadata = self.storage.load_metadata(model_dir)
        files = metadata.get("files", {})
        if files:
            print("  Verified Files:")
            for filename, file_info in files.items():
                print(f"    - {filename}: {file_info.get('hash', 'unknown')}")
        else:
            print("  Files: None verified")

    def delete_hash_file(self) -> bool:
        """Delete the storage directory.

        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            if self.storage.base_dir.exists():
                import shutil
                shutil.rmtree(self.storage.base_dir)
                print("Storage directory deleted successfully.")
                return True
            else:
                print("Storage directory does not exist.")
                return True
        except Exception as e:
            print(f"Error deleting storage directory: {e}")
            return False

    def get_unified_verification_result(self, target_spec: str) -> dict:
        """
        Get verification result for any model type (unified interface).

        Args:
            target_spec: Model specification (repo_id for HF, path for local)

        Returns:
            Unified verification result dictionary
        """
        # Auto-detect target type
        if self._is_local_path(target_spec):
            return self._verify_local_model(target_spec)
        else:
            return self._verify_hf_model(target_spec)

    def _is_local_path(self, target_spec: str) -> bool:
        """Check if target_spec is a local path."""
        return Path(target_spec).exists()

    def _verify_hf_model(self, repo_id: str) -> dict:
        """Verify HF model and return result."""
        from model_sentinel.target.hf import TargetHF

        target = TargetHF()
        revision = "main"  # Default revision for GUI

        new_model_hash = target.detect_model_changes(repo_id, revision)

        result = {
            "target_type": "hf",
            "repo_id": repo_id,
            "revision": revision,
            "status": "success",
            "model_hash_changed": bool(new_model_hash),
            "new_model_hash": new_model_hash,
            "files_verified": False,
            "message": "",
            "files_info": [],
            "display_info": [
                f"**Repository:** {repo_id}",
                f"**Revision:** {revision}"
            ]
        }

        if not new_model_hash:
            result["message"] = "No changes detected in the model hash."
            result["files_verified"] = True
        else:
            files_info = target.get_files_for_verification(repo_id, revision)
            result["files_info"] = files_info
            result["message"] = f"Found {len(files_info)} files that need verification."

        return result

    def _verify_local_model(self, model_dir: str) -> dict:
        """Verify local model and return result."""
        from model_sentinel.target.local import TargetLocal

        model_path = Path(model_dir)
        if not model_path.exists():
            raise FileNotFoundError(f"Model directory {model_dir} does not exist.")

        target = TargetLocal()
        new_model_hash = target.detect_model_changes(model_path)

        result = {
            "target_type": "local",
            "model_dir": str(model_path),
            "status": "success",
            "model_hash_changed": bool(new_model_hash),
            "new_model_hash": new_model_hash,
            "files_verified": False,
            "message": "",
            "files_info": [],
            "display_info": [
                f"**Model Directory:** {model_path}"
            ]
        }

        if not new_model_hash:
            result["message"] = "No changes detected in the model directory."
            result["files_verified"] = True
        else:
            files_info = target.get_files_for_verification(model_path)
            result["files_info"] = files_info
            result["message"] = f"Found {len(files_info)} files that need verification."

        return result

    def get_model_key_from_result(self, verification_result: dict) -> str:
        """Get model key from verification result."""
        target_type = verification_result.get("target_type")

        if target_type == "hf" or "repo_id" in verification_result:
            # HF model
            repo_id = verification_result["repo_id"]
            revision = verification_result.get("revision")
            return f"hf/{repo_id}@{revision}" if revision else f"hf/{repo_id}"
        elif target_type == "local" or "model_dir" in verification_result:
            # Local model - use storage manager to generate consistent ID
            model_path = Path(verification_result["model_dir"])
            model_id = self.storage.generate_local_model_dir_name(model_path)
            return f"local/{model_id}"
        else:
            raise ValueError("Unable to determine model type")
