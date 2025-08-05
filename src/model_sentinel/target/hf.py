from huggingface_hub import HfApi

from model_sentinel.target.base import TargetBase, VERIFICATION_FAILED_MESSAGE


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

        # Get directory for this model
        model_dir_path = self.directory_manager.get_hf_model_dir(repo_id, revision or "main")

        if not super().check_model_hash_changed(model_dir_path, current_hash):
            return None

        # Return current model hash to update later
        return current_hash

    def update_model_hash_for_repo(self, repo_id, revision, new_model_hash):
        """Update the model hash using directory system."""
        model_dir_path = self.directory_manager.get_hf_model_dir(repo_id, revision or "main")
        super().update_model_hash(model_dir_path, new_model_hash)

    def verify_remote_files(self, repo_id, revision=None) -> bool:
        """Check remote *.py files for changes and prompt for verification.

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

        # Get directory path for this model
        model_dir_path = self.directory_manager.get_hf_model_dir(repo_id, revision or "main")

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
        return self._verify_files_workflow(files_to_check, model_dir_path)

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
        """Generate repository key for data directory with hf/ prefix."""
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


def verify_hf_model(repo_id, revision=None, gui=False, exit_on_reject=True) -> bool:
    """
    Check if the model hash has changed and verify remote files.

    Args:
        repo_id: Hugging Face repository ID
        revision: Model revision/branch
        gui: If True, launch GUI for verification if needed
        exit_on_reject: If True, exit the process when verification fails

    Returns:
        bool: True if verification successful or no changes detected
    """

    target = TargetHF()
    new_model_hash = target.detect_model_changes(repo_id, revision=revision)

    # If no changes detected, model is already verified
    if not new_model_hash:
        print("No changes detected in the model hash. Model is already verified.")
        return True

    if gui:
        result = target.handle_gui_verification(repo_id=repo_id, revision=revision)
    else:
        result = _handle_cli_verification(target, repo_id, revision, new_model_hash)

    if not result and exit_on_reject:
        print(VERIFICATION_FAILED_MESSAGE)
        exit(1)

    return result


def _handle_cli_verification(
    target: TargetHF, repo_id: str, revision: str, new_model_hash: str
) -> bool:
    """Handle CLI-based verification."""
    print("\n" + "=" * 50)
    print("Checking remote Python files...")
    verified_all = target.verify_remote_files(repo_id, revision=revision)
    print(f"File check result: {verified_all}")

    if verified_all:
        target.update_model_hash_for_repo(repo_id, revision, new_model_hash)

        # Register in global registry
        model_key = f"{repo_id}@{revision or 'main'}"
        target.register_model_in_registry("hf", model_key)

        print("Verified model hash updated.")
        return True
    else:
        return False
