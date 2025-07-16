from huggingface_hub import HfApi

from model_sentinel.target.base import TargetBase


class TargetHF(TargetBase):
    """
    Target class for model-sentinel to track Hugging Face model changes.
    """

    def detect_model_changes(self, repo_id, revision=None) -> str | None:
        """
        Check if model hash has changed, and return the new hash if changed or new.

        Returns:
            New model hash if changed or new, None if no changes detected.
        """
        # Get the new model hash from Hugging Face API
        hf_api = HfApi()
        model_info = hf_api.model_info(repo_id=repo_id, revision=revision)
        current_hash = model_info.sha

        print(f"Checking repository: {repo_id}")
        if revision:
            print(f"Revision: {revision}")
        print(f"Current model hash: {current_hash}")

        # Load existing verified hashes
        repo_key = self._get_repo_key(repo_id, revision)
        data, _ = self.get_or_create_model_data(repo_key)

        if not super()._check_model_hash_changed(data, repo_key, current_hash):
            return None

        # Return current model hash to update later
        return current_hash

    def update_model_hash_for_repo(self, repo_id, revision, new_model_hash):
        """Update the model hash in the verified hashes file."""
        repo_key = self._get_repo_key(repo_id, revision)
        super().update_model_hash(repo_key, new_model_hash)

    def verify_remote_files(self, repo_id, revision=None) -> bool:
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

        repo_key = self._get_repo_key(repo_id, revision)

        # Prepare files for verification using common workflow
        files_to_check = []

        for sibling in model_info.siblings:
            if sibling.rfilename.endswith(".py"):
                content = self._download_file_content(
                    hf_api, repo_id, revision, sibling.rfilename
                )
                if content is not None:
                    files_to_check.append(
                        {
                            "filename": sibling.rfilename,
                            "hash": sibling.blob_id,
                            "content": content,
                        }
                    )
                else:
                    # If download failed, consider verification failed
                    return False

        # Use common verification workflow
        return self._verify_files_workflow(repo_key, files_to_check)

    def _download_file_content(self, hf_api, repo_id, revision, filename) -> str | None:
        """Download file content from HuggingFace.

        Returns:
            File content if successful, None if error.
        """
        print(f"Downloading file: {filename}")

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

    def _get_repo_key(self, repo_id, revision=None):
        """Generate repository key for data storage with hf/ prefix."""
        base_key = f"{repo_id}@{revision}" if revision else repo_id
        return f"hf/{base_key}"

    def get_files_for_verification(self, repo_id: str, revision: str = None):
        """
        Get list of HF model files that need verification for GUI display.

        Args:
            repo_id: Hugging Face repository ID
            revision: Model revision/branch

        Returns:
            List of file dictionaries with filename, content, and hash
        """
        files_info = []
        hf_api = HfApi()

        try:
            model_info = hf_api.model_info(
                repo_id=repo_id, revision=revision, files_metadata=True
            )

            for sibling in model_info.siblings:
                if sibling.rfilename.endswith(".py"):
                    content = self._download_file_content(
                        hf_api, repo_id, revision, sibling.rfilename
                    )
                    if content is not None:
                        files_info.append(
                            {
                                "filename": sibling.rfilename,
                                "content": content,
                                "hash": sibling.blob_id,
                            }
                        )
        except Exception as e:
            print(f"Error getting files for verification: {e}")

        return files_info


def verify_hf_model(repo_id, revision=None, gui=False) -> bool | dict:
    """
    Check if the model hash has changed and verify remote files.

    Args:
        repo_id: Hugging Face repository ID
        revision: Model revision/branch
        gui: If True, launch GUI for verification

    Returns:
        bool: True if verification successful (when gui=False)
        dict: Detailed verification results (when gui=True)
    """

    if gui:
        # Launch GUI for verification
        try:
            from model_sentinel.gui import launch_verification_gui

            launch_verification_gui(repo_id=repo_id, revision=revision)
            # Return a simple result since GUI handles the interaction
            return True
        except ImportError:
            print("GUI functionality requires gradio. Install with:")
            print("pip install 'model-sentinel[gui]'")
            return False

    # CLI mode: original behavior
    target = TargetHF()
    new_model_hash = target.detect_model_changes(repo_id, revision=revision)
    if not new_model_hash:
        print("No changes detected in the model hash. Skipping file checks.")
        return True

    print("\n" + "=" * 50)
    print("Checking remote Python files...")
    verified_all = target.verify_remote_files(repo_id, revision=revision)
    print(f"File check result: {verified_all}")

    if verified_all:
        target.update_model_hash_for_repo(repo_id, revision, new_model_hash)
        print("Verified model hash updated.")

    return verified_all


if __name__ == "__main__":
    # Set the current working directory to the project root
    import os
    from pathlib import Path

    project_dir = Path(__file__).parents[3]
    os.chdir(project_dir)
    print(f"Current working directory: {os.getcwd()}")

    # Example usage with Hugging Face model
    repo_id = "ryomo/malicious-code-test"
    revision = "main"
    verify_hf_model(repo_id, revision)
