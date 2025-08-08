import pydoc
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from model_sentinel.verify.metadata import compute_run_metadata
from model_sentinel.verify.session import build_session_files
from model_sentinel.verify.storage import StorageManager

FILES_NONE_VERIFIED = "  Files: None verified"


class Verify:
    """Base class for verifying model changes and file integrity."""

    def __init__(self):
        # Storage system
        self.storage = StorageManager()

    def _update_file_metadata(
        self, model_dir: Path, filename: str, file_hash: str, content: str
    ) -> None:
        """
        Update file content (and legacy metadata when applicable).

        Args:
            model_dir: Model directory
            filename: Name of the file
            file_hash: File hash
            content: File content
        """
        # Save file content
        self.storage.save_file_content(model_dir, filename, content)

        # Note: New metadata schema is written after verification flow completes.
        # For backward compatibility with existing metadata, keep minimal legacy fields
        # when an old-style dict format is detected.
        metadata = self.storage.load_metadata(model_dir)
        files_entry = metadata.get("files")
        if isinstance(files_entry, dict):
            files_entry[filename] = {
                "hash": file_hash,
                "size": len(content.encode("utf-8")),
                "verified_at": self.storage.get_current_timestamp(),
            }
            metadata["last_verified"] = self.storage.get_current_timestamp()
            self.storage.save_metadata(model_dir, metadata)

    def verify_file(
        self, filename: str, current_hash: str, content: str, model_dir: Path
    ) -> bool:
        """Verify file content and update storage if confirmed.

        Args:
            filename: Name of the file being verified
            current_hash: Current hash of the file
            content: File content
            model_dir: Model directory

        Returns:
            True if file is verified and storage updated, False otherwise.
        """

        def prompt_user_verification(item_name, content):
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

        if prompt_user_verification(filename, content):
            self._update_file_metadata(model_dir, filename, current_hash, content)
            print("Trust confirmed. File content and hash updated.")
            return True
        else:
            print("Trust not confirmed. Please review the file changes.")
            return False

    def update_model_hash(self, model_dir: Path, new_hash: str) -> None:
        """Update model hash in metadata.

        Args:
            model_dir: Model directory
            new_hash: New model hash
        """
        metadata = self.storage.load_metadata(model_dir)
        metadata["model_hash"] = new_hash
        metadata["last_verified"] = self.storage.get_current_timestamp()
        self.storage.save_metadata(model_dir, metadata)
        print(f"Model hash updated to: {new_hash}")

    def check_file_changed(
        self, model_dir: Path, filename: str, current_hash: str
    ) -> bool:
        """Check if file hash has changed in storage system.

        Args:
            model_dir: Model directory
            filename: Filename to check
            current_hash: Current file hash

        Returns:
            True if file changed or is new, False if unchanged
        """
        metadata = self.storage.load_metadata(model_dir)
        files_entry = metadata.get("files", {})
        file_info = None
        if isinstance(files_entry, dict):
            file_info = files_entry.get(filename)
        elif isinstance(files_entry, list):
            for item in files_entry:
                if item.get("path") == filename:
                    file_info = item
                    break

        if file_info is None:
            print(f"No previous hash found for {filename}. This is the first check.")
            return True

        previous_hash = file_info.get("hash")
        if previous_hash == current_hash:
            print(f"No changes detected in {filename}.")
            return False

        print(f"Changes detected in {filename}!")
        return True

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

    def _display_model_info(self, model_key: str, model_info: dict[str, Any]) -> None:
        """Display information for a single model."""
        print(f"\nModel: {model_key}")
        print(f"Type: {model_info.get('type', 'unknown')}")
        print(f"Last Verified: {model_info.get('last_verified', 'unknown')}")
        print(f"Status: {model_info.get('status', 'unknown')}")

        if model_info.get("original_path"):
            print(f"Original Path: {model_info['original_path']}")

        # Get model directory
        model_dir = self._resolve_model_dir(model_key=model_key, model_info=model_info)
        if model_dir and model_dir.exists():
            self._display_file_info(model_dir)
        else:
            print("  Files: Metadata not found")

    def _resolve_model_dir(
        self,
        verification_result: dict = None,
        model_key: str = None,
        model_info: dict = None,
    ) -> Path | None:
        """Resolve model directory from verification result or model info."""
        if verification_result:
            if verification_result.get("target_type") == "local":
                return self.storage.get_local_model_dir(Path(verification_result["model_dir"]))
            else:
                return self.storage.get_hf_model_dir(
                    verification_result["repo_id"],
                    verification_result.get("revision", "main")
                )

        elif model_key and model_info:
            model_type = model_info.get("type")
            if model_type == "local":
                return self.storage.local_dir / model_key.split("/", 1)[1]
            elif model_type == "hf":
                model_path = model_key.split("/", 1)[1]
                repo_parts, revision = model_path.rsplit("@", 1) if "@" in model_path else (model_path, "main")
                return self.storage.get_hf_model_dir(repo_parts, revision)

        return None

    def _display_file_info(self, model_dir: Path) -> None:
        """Display file information for a model."""
        metadata = self.storage.load_metadata(model_dir)
        files_entry = metadata.get("files", {})
        if isinstance(files_entry, dict):
            files = files_entry
            if files:
                print("  Verified Files:")
                for filename, file_info in files.items():
                    print(f"    - {filename}: {file_info.get('hash', 'unknown')}")
            else:
                print(FILES_NONE_VERIFIED)
        elif isinstance(files_entry, list):
            files_list = files_entry
            if files_list:
                print("  Verified Files:")
                for item in files_list:
                    print(f"    - {item.get('path', 'unknown')}: {item.get('hash', 'unknown')}")
            else:
                print(FILES_NONE_VERIFIED)
        else:
            print(FILES_NONE_VERIFIED)

    def delete_hash_file(self) -> bool:
        """Delete the directory.

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
            print(f"Error deleting directory: {e}")
            return False

    def _verify_model_template(
        self, target, detect_args: tuple, verify_args: tuple, display_info: list[str]
    ) -> dict:
        """Template method for model verification.

        Args:
            target: Target instance (HF or Local)
            detect_args: Arguments for detect_model_changes (as tuple)
            verify_args: Arguments for get_files_for_verification (as tuple)
            display_info: Information to display in result

        Returns:
            Verification result dictionary
        """
        new_model_hash = target.detect_model_changes(*detect_args)

        result = {
            "status": "success",
            "model_hash_changed": bool(new_model_hash),
            "new_model_hash": new_model_hash,
            "files_verified": False,
            "message": "",
            "files_info": [],
            "display_info": display_info,
        }

        if not new_model_hash:
            result["message"] = "No changes detected in the model hash."
            result["files_verified"] = True
        else:
            files_info = target.get_files_for_verification(*verify_args)
            result["files_info"] = files_info
            result["message"] = f"Found {len(files_info)} files that need verification."

        return result

    def _determine_target_from_model_dir(self, model_dir: Path) -> tuple[str, str]:
        """Infer target type and id from model_dir path.

        Returns: (type, id) where id is path relative to base_dir (hf/... or local/...).
        """
        try:
            rel = model_dir.relative_to(self.storage.base_dir)
            parts = rel.parts
            if len(parts) >= 1:
                t = parts[0]
                return t, "/".join(parts[1:])
        except Exception:
            pass
        return "unknown", str(model_dir)

    def save_run_metadata(self, model_dir: Path, session_files: list[dict[str, Any]]) -> None:
        """Persist metadata.json for this verification run.

        session_files: list of {filename, hash, content, approved(bool)}
        """
        # Resolve tool version without creating circular imports
        def _resolve_tool_version() -> str:
            try:
                try:
                    # Python 3.8+
                    from importlib.metadata import version  # type: ignore
                except ImportError:  # pragma: no cover
                    from importlib_metadata import version  # type: ignore
                return version("model-sentinel")
            except Exception:
                try:
                    from model_sentinel import __version__ as v  # type: ignore
                    return v
                except Exception:
                    return "unknown"
        # Load existing metadata (support old/new)
        existing = self.storage.load_metadata(model_dir)

        t_type, t_id = self._determine_target_from_model_dir(model_dir)
        new_meta = compute_run_metadata(
            existing,
            session_files,
            target_type=t_type,
            target_id=t_id,
            tool_version=_resolve_tool_version(),
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            current_timestamp=self.storage.get_current_timestamp(),
        )
        # Fill run_id at the boundary
        if isinstance(new_meta.get("run"), dict):
            new_meta["run"]["run_id"] = str(uuid.uuid4())

        self.storage.save_metadata(model_dir, new_meta)

    def verify_hf_model(self, repo_id: str, revision: str = "main") -> dict:
        """Verify HF model and return result."""
        from model_sentinel.target.hf import TargetHF

        target = TargetHF()
        detect_args = (repo_id, revision)
        verify_args = (repo_id, revision)
        display_info = [f"**Repository:** {repo_id}", f"**Revision:** {revision}"]

        result = self._verify_model_template(
            target, detect_args, verify_args, display_info
        )
        result.update({"target_type": "hf", "repo_id": repo_id, "revision": revision})
        return result

    def verify_local_model(self, model_dir: str) -> dict:
        """Verify local model and return result."""
        from model_sentinel.target.local import TargetLocal

        model_path = Path(model_dir)
        if not model_path.exists():
            raise FileNotFoundError(f"Model directory {model_dir} does not exist.")

        target = TargetLocal()
        detect_args = (model_path,)
        verify_args = (model_path,)
        display_info = [f"**Model Directory:** {model_path}"]

        result = self._verify_model_template(
            target, detect_args, verify_args, display_info
        )
        result.update({"target_type": "local", "model_dir": str(model_path)})
        return result

    def get_model_key_from_result(self, verification_result: dict) -> str:
        """Get model key from verification result."""
        if verification_result.get("target_type") == "hf" or "repo_id" in verification_result:
            model_id = f"{verification_result['repo_id']}@{verification_result.get('revision', 'main')}"
            return self.storage.get_model_key("hf", model_id)
        elif verification_result.get("target_type") == "local" or "model_dir" in verification_result:
            model_id = self.storage.generate_local_model_dir_name(Path(verification_result["model_dir"]))
            return self.storage.get_model_key("local", model_id)
        else:
            raise ValueError("Unable to determine model type")

    def save_verification_results(
        self, verification_result: dict[str, Any], approved_files: list[str]
    ) -> str:
        """
        Save verification results using the directory system.

        Args:
            verification_result: Original verification result
            approved_files: List of approved filenames

        Returns:
            Status message
        """
        if not verification_result.get("model_hash_changed"):
            return "No changes to save."

        try:
            print(
                f"🔍 Saving verification results for {len(approved_files)} approved files: {approved_files}"
            )

            # Determine model key and get directory
            model_key = self.get_model_key_from_result(verification_result)
            print(f"🔑 Model key: {model_key}")

            # Get model directory
            model_dir = self._resolve_model_dir(verification_result=verification_result)

            # Update model hash if changed
            if verification_result.get("new_model_hash"):
                self.update_model_hash(model_dir, verification_result["new_model_hash"])
                print(
                    f"🔄 Updated model hash: {verification_result['new_model_hash'][:16]}..."
                )

            # Update file hashes for approved files using directory system
            approved_count = self._update_approved_files_directory(
                model_dir, verification_result, approved_files
            )

            # Also write metadata report for this session using same model_dir
            self.write_session_metadata(verification_result, approved_files, model_dir=model_dir)

            # Register model in registry
            model_type, model_id = model_key.split("/", 1)
            kwargs = {}
            if verification_result.get("target_type") == "local":
                kwargs["original_path"] = verification_result["model_dir"]
            self.storage.register_model(model_type, model_id, **kwargs)

            print("💾 Saved verification data to storage system")
            return (
                f"✅ Verification completed! {approved_count} files approved and saved."
            )

        except Exception as e:
            error_msg = f"❌ Error saving verification results: {str(e)}"
            print(error_msg)
            return error_msg

    def _update_approved_files_directory(
        self,
        model_dir: Path,
        verification_result: dict[str, Any],
        approved_files: list[str],
    ) -> int:
        """Update file hashes for approved files using storage system."""
        files_info = verification_result.get("files_info", [])
        approved_count = 0

        for file_info in files_info:
            filename = file_info.get("filename", "")
            file_hash = file_info.get("hash", "")
            content = file_info.get("content", "")

            if filename in approved_files and file_hash:
                self._update_file_metadata(model_dir, filename, file_hash, content)
                approved_count += 1
                print(f"✅ Approved file: {filename} - {file_hash[:16]}...")

        return approved_count

    def write_session_metadata(
        self,
        verification_result: dict[str, Any],
        approved_files: list[str],
        *,
        model_dir: Path | None = None,
    ) -> None:
        if model_dir is None:
            model_dir = self._resolve_model_dir(verification_result=verification_result)
            if model_dir is None:
                return
        session = build_session_files(
            verification_result.get("files_info", []), approved_files
        )
        self.save_run_metadata(model_dir, session)
