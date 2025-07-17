import json
from pathlib import Path
import pydoc


class Verify:
    """Base class for verifying model changes and file integrity."""

    def __init__(self):
        self.verified_hashes_file = Path(".model-sentinel.json")

    def verify_file(self, filename, current_hash, content, data, repo_key):
        """Prompt user for verification and update hash if confirmed.

        Returns:
            True if file is verified and hash updated, False otherwise.
        """
        if self.prompt_user_verification(filename, content):
            data[repo_key]["files"][filename] = current_hash
            print("Trust confirmed. Hash updated.")
            return True
        else:
            print("Trust not confirmed. Please review the file changes.")
            return False

    def load_verified_hashes(self):
        """Load all verified hashes from JSON file."""
        if not self.verified_hashes_file.exists():
            return {}

        with open(self.verified_hashes_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_verified_hashes(self, data):
        """Save verified hashes to JSON file."""
        with open(self.verified_hashes_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

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
        """Display all verified hashes in a human-readable format."""
        data = self.load_verified_hashes()

        if not data:
            print("No verified hashes found.")
            return

        print("=== Verified Hashes Summary ===")
        for repo_key, repo_data in data.items():
            print(f"\nRepository: {repo_key}")
            if repo_data.get("revision"):
                print(f"Revision: {repo_data['revision']}")

            if repo_data.get("model_hash"):
                print(f"Model Hash: {repo_data['model_hash']}")
            else:
                print("Model Hash: Not verified")

            files = repo_data.get("files", {})
            if files:
                print("Verified Files:")
                for filename, file_hash in files.items():
                    print(f"  - {filename}: {file_hash}")
            else:
                print("Files: None verified")
            print("-" * 50)

    def delete_hash_file(self) -> bool:
        """Delete the hash file (the list of verified files).

        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            if self.verified_hashes_file.exists():
                self.verified_hashes_file.unlink()
            return True
        except Exception as e:
            print(f"Error deleting hash file: {e}")
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
        from pathlib import Path
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
            # Local model
            model_dir = verification_result["model_dir"]
            return f"local/{model_dir}"
        else:
            raise ValueError("Unable to determine model type")
