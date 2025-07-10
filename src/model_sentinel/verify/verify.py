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
