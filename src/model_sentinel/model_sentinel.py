import json
import pydoc
import shutil
from pathlib import Path

from huggingface_hub import HfApi
from platformdirs import user_data_dir


class ModelSentinel:
    """Model sentinel for tracking model changes."""

    def __init__(self):
        app_name = "model-sentinel"

        # Initialize data directory
        self.data_dir = Path(user_data_dir(app_name))
        self.verified_hashes_file = self.data_dir / "verified_hashes.json"

    def check_model_hash_changed(self, repo_id, revision=None) -> bool:
        """Check if model hash has changed.

        Returns:
            True if model hash changed or is new, False if unchanged.
        """
        hf_api = HfApi()
        model_info = hf_api.model_info(repo_id=repo_id, revision=revision)
        current_model_hash = model_info.sha

        print(f"Checking repository: {repo_id}")
        if revision:
            print(f"Revision: {revision}")
        print(f"Current model hash: {current_model_hash}")

        data, repo_key = self._get_repo_data(repo_id, revision)
        saved_model_hash = data[repo_key]["model_hash"]

        if saved_model_hash == current_model_hash:
            print("No changes detected. Model is up to date.")
            return False

        if saved_model_hash is None:
            print("No previous model hash found. This is the first check.")
        else:
            print("Changes detected!")
            print(f"Previous hash: {saved_model_hash}")
            print(f"Current hash:  {current_model_hash}")

        return True

    def check_remote_files(self, repo_id, revision=None) -> bool:
        """Check remote .py files for changes and prompt for verification.

        Returns:
            True if all files are verified, False otherwise.
        """
        hf_api = HfApi()
        model_info = hf_api.model_info(
            repo_id=repo_id, revision=revision, files_metadata=True
        )

        print(f"Checking Python files in repository: {repo_id}")
        if revision:
            print(f"Revision: {revision}")

        data, repo_key = self._get_repo_data(repo_id, revision)
        all_verified = True

        # Check each .py file
        for sibling in model_info.siblings:
            if sibling.rfilename.endswith(".py"):
                file_content = self._check_single_file(
                    hf_api,
                    repo_id,
                    revision,
                    sibling.rfilename,
                    sibling.blob_id,
                    data,
                    repo_key,
                )
                if file_content is not None:
                    file_verified = self._verify_file(
                        sibling.rfilename, sibling.blob_id, file_content, data, repo_key
                    )
                    if not file_verified:
                        all_verified = False
                else:
                    all_verified = False

        self._save_verified_hashes(data)
        return all_verified

    def _check_single_file(
        self, hf_api, repo_id, revision, filename, current_hash, data, repo_key
    ):
        """Check a single file for changes and download if needed.

        Returns:
            File content if file needs verification, None if unchanged or error.
        """
        print(f"\nChecking file: {filename}")
        print(f"Current hash: {current_hash}")

        saved_hash = data[repo_key]["files"].get(filename)

        if saved_hash == current_hash:
            print("No changes detected. File is up to date.")
            return None

        if saved_hash is None:
            print("No previous hash found. This is the first check.")
        else:
            print("Changes detected!")
            print(f"Previous hash: {saved_hash}")
            print(f"Current hash:  {current_hash}")

        # Download and get file content
        try:
            file_path = hf_api.hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                revision=revision,
            )

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return content

        except Exception as e:
            print(f"Error downloading file {filename}: {e}")
            return None

    def _verify_file(self, filename, current_hash, content, data, repo_key):
        """Prompt user for verification and update hash if confirmed.

        Returns:
            True if file is verified and hash updated, False otherwise.
        """
        if self._prompt_user_verification(filename, content):
            data[repo_key]["files"][filename] = current_hash
            print("Trust confirmed. Hash updated.")
            return True
        else:
            print("Trust not confirmed. Please review the file changes.")
            return False

    def _load_verified_hashes(self):
        """Load all verified hashes from JSON file."""
        if not self.verified_hashes_file.exists():
            return {}

        with open(self.verified_hashes_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_verified_hashes(self, data):
        """Save verified hashes to JSON file."""
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)

        with open(self.verified_hashes_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_repo_data(self, repo_id, revision=None):
        """Get repository data structure from saved hashes."""
        data = self._load_verified_hashes()
        repo_key = f"{repo_id}@{revision}" if revision else repo_id

        if repo_key not in data:
            data[repo_key] = {
                "repo_id": repo_id,
                "revision": revision,
                "model_hash": None,
                "files": {},
            }

        return data, repo_key

    def _prompt_user_verification(self, item_name, content):
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
        data = self._load_verified_hashes()

        if not data:
            print("No verified hashes found.")
            return

        print("=== Verified Hashes Summary ===")
        for repo_key, repo_data in data.items():
            print(f"\nRepository: {repo_data['repo_id']}")
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

    def delete_data_dir(self) -> bool:
        """Delete the data directory.

        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            if self.data_dir.exists():
                shutil.rmtree(self.data_dir)
            return True
        except Exception as e:
            print(f"Error deleting data directory: {e}")
            return False


def check(repo_id, revision=None) -> bool:
    """
    Check if the model hash has changed and verify remote files.
    """
    sentinel = ModelSentinel()
    model_changed = sentinel.check_model_hash_changed(repo_id, revision=revision)
    if not model_changed:
        print("No changes detected in the model hash. Skipping file checks.")
        return True

    print("\n" + "=" * 50)
    print("Checking remote Python files...")
    verified_all = sentinel.check_remote_files(repo_id, revision=revision)
    print(f"File check result: {verified_all}")

    return verified_all


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Model Sentinel CLI")
    parser.add_argument(
        "--delete-data-dir", action="store_true", help="Delete the data directory"
    )
    parser.add_argument(
        "--check-files-only", action="store_true", help="Only check remote files"
    )
    parser.add_argument(
        "--list-verified", action="store_true", help="List all verified hashes"
    )
    args = parser.parse_args()

    REPO_NAME = "ryomo/malicious-code-test"
    REVISION = "main"

    if args.delete_data_dir:
        # Delete the data directory
        sentinel = ModelSentinel()
        result = sentinel.delete_data_dir()
        if result:
            print("Data directory deleted.")
        else:
            print("Failed to delete data directory.")

    elif args.list_verified:
        # List all verified hashes
        sentinel = ModelSentinel()
        sentinel.list_verified_hashes()

    elif args.check_files_only:
        # Check remote files only without checking model hash
        sentinel = ModelSentinel()
        result = sentinel.check_remote_files(REPO_NAME, revision=REVISION)
        print(f"File check result: {result}")

    else:
        # Default behavior: check model hash then files
        print(f"Using repository: {REPO_NAME} at revision: {REVISION}")

        if not check(REPO_NAME, REVISION):
            print(f"Repository {REPO_NAME} at revision {REVISION} is not verified.")
            print("Please verify all remote files in the repository before proceeding.")


if __name__ == "__main__":
    main()
