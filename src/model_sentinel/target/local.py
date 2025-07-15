import hashlib
from pathlib import Path

from model_sentinel import Verify
from model_sentinel.target.base import TargetBase


class TargetLocal(TargetBase):
    """Target class for model-sentinel to track local model changes."""

    def _get_directory_hash(self, directory: str, file_type: str = "*.py") -> str:
        """
        Calculate a hash for all files in the given directory matching the file_type.

        Args:
            directory (str): Path to the directory to hash.
            file_type (str): Glob pattern to match files (default: "*.py").

        Returns:
            str: Hexadecimal hash of the directory contents.
        """
        hash_obj = hashlib.sha256()
        directory_path = Path(directory)
        for fpath in directory_path.rglob(file_type):
            # Add the relative path to the hash
            rel_path = fpath.relative_to(directory_path)
            hash_obj.update(str(rel_path).encode())
            with open(fpath, "rb") as f:
                while chunk := f.read(8192):
                    hash_obj.update(chunk)

        return hash_obj.hexdigest()

    def _get_file_hash(self, file_path: str, file_type: str = "*.py") -> str:
        """
        Calculate a hash for the given file.

        Args:
            file_path (str): Path to the file to hash.
            file_type (str): Glob pattern to match files (default: "*.py").

        Returns:
            str: Hexadecimal hash of the file contents.
        """
        if not Path(file_path).match(file_type):
            raise ValueError(f"File {file_path} does not match the pattern {file_type}")

        hash_obj = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    def _get_file_list(self, directory: str, file_type: str = "*.py") -> list[Path]:
        """
        Get a list of files in the given directory matching the file_type.

        Args:
            directory (str): Path to the directory to search.
            file_type (str): Glob pattern to match files (default: "*.py").

        Returns:
            list[Path]: List of file paths matching the file_type.
        """
        directory_path = Path(directory)
        file_list = list(directory_path.rglob(file_type))
        return file_list


def check_local(model_dir: str | Path) -> bool:

    model_dir = Path(model_dir)
    print(f"Model directory: {model_dir}")

    # Check if the model directory exists
    if not model_dir.exists():
        print(f"Model directory {model_dir} does not exist.")
        return False

    print(f"Checking model: {model_dir.name}")

    # Load existing verified hashes
    verify = Verify()
    data = verify.load_verified_hashes()
    model_id = f"local/{model_dir}"
    if model_id not in data:
        print(f'Model "{model_id}" not found in verified hashes. Initializing.')
        data[model_id] = {
            "model_id": model_id,
            "model_hash": None,
            "files": {},
        }

    # Get the directory hash
    target = TargetLocal()
    dir_hash = target._get_directory_hash(str(model_dir), "*.py")
    print(f"Directory hash: {dir_hash}")

    # Check if the directory hash has changed
    if data[model_id]["model_hash"] == dir_hash:
        print("No changes detected in the model directory.")
        return True

    # Compare the current hash with the saved hash
    all_verified = True
    file_list = target._get_file_list(str(model_dir), "*.py")
    for file_path in file_list:
        file_hash = target._get_file_hash(file_path, "*.py")
        relative_file_path = file_path.relative_to(model_dir)
        print(f"File: {relative_file_path}, Hash: {file_hash}")

        previous_file_hash = data[model_id]["files"].get(str(relative_file_path))
        if previous_file_hash == file_hash:
            print(f"No changes detected in {relative_file_path}.")
            continue

        elif previous_file_hash is None:
            print(
                f"No previous hash found for {relative_file_path}. This is the first check."
            )

        else:
            print(f"Changes detected in {relative_file_path}!")

        content = file_path.read_text(encoding="utf-8")
        file_verified = verify.verify_file(
            str(relative_file_path), file_hash, content, data, model_id
        )
        if file_verified:
            data[model_id]["files"][str(relative_file_path)] = file_hash
        else:
            all_verified = False

    if all_verified:
        data[model_id]["model_hash"] = dir_hash
        verify.save_verified_hashes(data)
        print(f"Model hash updated to: {dir_hash}")
    else:
        print("Some files were not verified. Please review the changes.")

    return all_verified


if __name__ == "__main__":
    # Set the current working directory to the project root
    import os
    project_dir = Path(__file__).parents[3]
    os.chdir(project_dir)
    print(f"Current working directory: {os.getcwd()}")

    # Example usage
    model_dir = "downloaded_model/malicious-code-test-hf"
    check_local(model_dir)
