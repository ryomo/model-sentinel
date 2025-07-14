from huggingface_hub import HfApi

from model_sentinel.target.base import TargetBase


class TargetHF(TargetBase):
    """Target class for model-sentinel to track Hugging Face model changes."""

    def check_model_hash_changed(self, repo_id, revision=None) -> str | None:
        """
        Check if model hash has changed, and return the new hash if changed or new.

        Returns:
            New model hash if changed or new, None if no changes detected.
        """
        # Get the new model hash from Hugging Face API
        hf_api = HfApi()
        model_info = hf_api.model_info(repo_id=repo_id, revision=revision)
        new_model_hash = model_info.sha

        print(f"Checking repository: {repo_id}")
        if revision:
            print(f"Revision: {revision}")
        print(f"New model hash: {new_model_hash}")

        # Load existing verified hashes
        data, repo_key = self._get_repo_data(repo_id, revision)
        old_model_hash = data[repo_key].get("model_hash")

        if old_model_hash == new_model_hash:
            print("No changes detected. Model is up to date.")
            return None

        if old_model_hash is None:
            print("No previous model hash found. This is the first check.")
        else:
            print("Changes detected!")
            print(f"Previous hash: {old_model_hash}")
            print(f"New hash:  {new_model_hash}")

        # Return current model hash to update later, if changed or is new
        return new_model_hash

    def update_model_hash(self, repo_id, revision, new_model_hash):
        """Update the model hash in the verified hashes file."""
        data, repo_key = self._get_repo_data(repo_id, revision)
        data[repo_key]["model_hash"] = new_model_hash
        self.verify.save_verified_hashes(data)

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
                    file_verified = self.verify.verify_file(
                        sibling.rfilename, sibling.blob_id, file_content, data, repo_key
                    )
                    if not file_verified:
                        all_verified = False
                else:
                    all_verified = False

        self.verify.save_verified_hashes(data)
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

    def _get_repo_data(self, repo_id, revision=None):
        """Get repository data structure from saved hashes."""
        data = self.verify.load_verified_hashes()
        repo_key = f"{repo_id}@{revision}" if revision else repo_id

        if repo_key not in data:
            data[repo_key] = {
                "repo_id": repo_id,
                "revision": revision,
                "model_hash": None,
                "files": {},
            }

        return data, repo_key


def check_hf(repo_id, revision=None) -> bool:
    """
    Check if the model hash has changed and verify remote files.
    """
    target = TargetHF()
    new_model_hash = target.check_model_hash_changed(repo_id, revision=revision)
    if not new_model_hash:
        print("No changes detected in the model hash. Skipping file checks.")
        return True

    print("\n" + "=" * 50)
    print("Checking remote Python files...")
    verified_all = target.check_remote_files(repo_id, revision=revision)
    print(f"File check result: {verified_all}")

    if verified_all:
        target.update_model_hash(repo_id, revision, new_model_hash)
        print("Verified model hash updated.")

    return verified_all
