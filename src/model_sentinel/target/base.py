import hashlib
from pathlib import Path

from model_sentinel.verify.verify import Verify

# Constants
VERIFICATION_FAILED_MESSAGE = "Model verification failed. Exiting for security reasons."


class TargetBase:
    """
    Base class for all target implementations.
    """

    def __init__(self):
        self.verify = Verify()

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
        self, model_key: str, files_to_check: list[dict]
    ) -> bool:
        """
        Common workflow for verifying multiple files.

        Args:
            model_key: Model identifier
            files_to_check: List of dicts with 'path', 'filename', 'hash', 'content'

        Returns:
            bool: True if all files verified successfully
        """
        data, _ = self.get_or_create_model_data(model_key)
        all_verified = True

        for file_info in files_to_check:
            filename = file_info["filename"]
            file_hash = file_info["hash"]
            content = file_info["content"]

            print(f"File: {filename}, Hash: {file_hash}")

            if not self._check_file_changed(data, model_key, filename, file_hash):
                continue

            file_verified = self.verify_and_update_file_hash(
                data, model_key, filename, file_hash, content
            )
            if not file_verified:
                all_verified = False

        self.verify.save_verified_hashes(data)
        return all_verified

    def get_or_create_model_data(self, model_key: str) -> tuple[dict, str]:
        """
        Get existing model data or create new one.

        Args:
            model_key: Unique identifier for the model

        Returns:
            tuple: (data_dict, model_key)
        """
        data = self.verify.load_verified_hashes()

        if model_key not in data:
            print(f'Model "{model_key}" not found in verified hashes. Initializing.')
            # Only store essential data to avoid redundancy
            data[model_key] = {"model_hash": None, "files": {}}

        return data, model_key

    def _check_model_hash_changed(
        self, data: dict, model_key: str, current_hash: str
    ) -> bool:
        """
        Check if model hash has changed.

        Args:
            data: Loaded hash data
            model_key: Model identifier
            current_hash: Current hash to compare

        Returns:
            bool: True if hash changed or is new, False if unchanged
        """
        previous_hash = data[model_key]["model_hash"]

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

    def _check_file_changed(
        self, data: dict, model_key: str, filename: str, current_hash: str
    ) -> bool:
        """
        Check if file hash has changed.

        Args:
            data: Loaded hash data
            model_key: Model identifier
            filename: File name to check
            current_hash: Current file hash

        Returns:
            bool: True if file changed or is new, False if unchanged
        """
        previous_hash = data[model_key]["files"].get(filename)

        if previous_hash == current_hash:
            print(f"No changes detected in {filename}.")
            return False

        if previous_hash is None:
            print(f"No previous hash found for {filename}. This is the first check.")
        else:
            print(f"Changes detected in {filename}!")

        return True

    def update_model_hash(self, model_key: str, new_hash: str):
        """Update model hash and save to file."""
        data = self.verify.load_verified_hashes()
        data[model_key]["model_hash"] = new_hash
        self.verify.save_verified_hashes(data)
        print(f"Model hash updated to: {new_hash}")

    def verify_and_update_file_hash(
        self, data: dict, model_key: str, filename: str, file_hash: str, content: str
    ) -> bool:
        """
        Verify file content and update hash if verified.

        Returns:
            bool: True if file was verified and hash updated
        """
        file_verified = self.verify.verify_file(
            filename, file_hash, content, data, model_key
        )
        return file_verified
