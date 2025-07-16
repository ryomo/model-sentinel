from pathlib import Path
from typing import Dict, List

from model_sentinel.target.base import TargetBase


class TargetLocal(TargetBase):
    """
    Target class for model-sentinel to track local model changes.
    """

    def detect_model_changes(self, model_dir: Path) -> str | None:
        """
        Check if local model hash has changed, and return the new hash if changed or new.

        Returns:
            New model hash if changed or new, None if no changes detected.
        """
        print(f"Model directory: {model_dir}")
        print(f"Checking model: {model_dir.name}")

        # Get the directory hash using base class method
        current_hash = self._calculate_directory_hash(model_dir, "*.py")
        print(f"Directory hash: {current_hash}")

        # Load existing verified hashes
        model_key = self._get_model_key(model_dir)
        data, _ = self.get_or_create_model_data(model_key)

        if not super()._check_model_hash_changed(data, model_key, current_hash):
            return None

        # Return current model hash to update later
        return current_hash

    def verify_local_files(self, model_dir: Path) -> bool:
        """
        Check local .py files for changes and prompt for verification.

        Returns:
            True if all files are verified, False otherwise.
        """
        print(f"Checking Python files in directory: {model_dir}")

        model_key = self._get_model_key(model_dir)

        # Prepare files for verification using common workflow
        files_to_check = []
        file_paths = self._get_files_by_pattern(model_dir, "*.py")

        for file_path in file_paths:
            file_hash = self._calculate_file_hash(file_path)
            relative_file_path = file_path.relative_to(model_dir)
            filename = str(relative_file_path)
            content = self._read_file_content(file_path)

            files_to_check.append(
                {
                    "path": file_path,
                    "filename": filename,
                    "hash": file_hash,
                    "content": content,
                }
            )

        # Use common verification workflow
        return self._verify_files_workflow(model_key, files_to_check)

    def _get_model_key(self, model_dir: Path) -> str:
        """Generate model key for data storage."""
        return f"local/{model_dir}"

    def get_files_for_verification(self, model_dir: Path) -> List[Dict[str, str]]:
        """
        Get list of files that need verification for GUI display.

        Args:
            model_dir: Path to the local model directory

        Returns:
            List of file dictionaries with filename, content, and hash
        """
        files_info = []
        file_paths = self._get_files_by_pattern(model_dir, "*.py")

        for file_path in file_paths:
            file_hash = self._calculate_file_hash(file_path)
            relative_file_path = file_path.relative_to(model_dir)
            filename = str(relative_file_path)
            content = self._read_file_content(file_path)

            files_info.append(
                {
                    "filename": filename,
                    "content": content,
                    "hash": file_hash,
                    "path": str(file_path),
                }
            )

        return files_info


def verify_local_model(model_dir: str | Path, gui=False) -> bool | dict:
    """
    Check if the local model hash has changed and verify local files.

    Args:
        model_dir: Path to the local model directory
        gui: If True, return detailed results for GUI display

    Returns:
        bool: True if verification successful (when gui=False)
        dict: Detailed verification results (when gui=True)
    """
    model_dir = Path(model_dir)

    # Check if the model directory exists
    if not model_dir.exists():
        error_msg = f"Model directory {model_dir} does not exist."
        if gui:
            return {
                "model_dir": str(model_dir),
                "status": "error",
                "model_hash_changed": False,
                "files_verified": False,
                "message": error_msg,
                "files_info": [],
            }
        else:
            print(error_msg)
            return False

    target = TargetLocal()
    new_model_hash = target.detect_model_changes(model_dir)

    if gui:
        # Launch GUI for verification
        try:
            from model_sentinel.gui import launch_verification_gui

            launch_verification_gui(model_dir=str(model_dir))
            # Return a simple result since GUI handles the interaction
            return True
        except ImportError:
            print("GUI functionality requires gradio. Install with:")
            print("pip install 'model-sentinel[gui]'")
            return False
    # CLI mode: original behavior
    if not new_model_hash:
        print("No changes detected in the model directory.")
        return True

    print("\n" + "=" * 50)
    print("Checking local Python files...")
    verified_all = target.verify_local_files(model_dir)
    print(f"File check result: {verified_all}")

    if verified_all:
        model_key = target._get_model_key(model_dir)
        target.update_model_hash(model_key, new_model_hash)
        print("Verified model hash updated.")

    return verified_all


if __name__ == "__main__":
    # Set the current working directory to the project root
    import os

    project_dir = Path(__file__).parents[3]
    os.chdir(project_dir)
    print(f"Current working directory: {os.getcwd()}")

    # Example usage
    model_dir = "downloaded_model/malicious-code-test-hf"
    verify_local_model(model_dir)
