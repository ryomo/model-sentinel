from pathlib import Path

from model_sentinel.target.base import TargetBase, VERIFICATION_FAILED_MESSAGE


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

        # Get directory for this model
        model_dir_path = self.get_model_directory_path(
            f"local/{self.storage.generate_local_model_dir_name(model_dir)}", model_dir
        )

        if not super().check_model_hash_changed(model_dir_path, current_hash):
            return None

        # Return current model hash to update later
        return current_hash

    def verify_local_files(self, model_dir: Path) -> bool:
        """
        Check local *.py files for changes and prompt for verification.

        Returns:
            True if all files are verified, False otherwise.
        """
        print(f"Checking Python files in directory: {model_dir}")

        # Get directory for this model
        model_key = self._get_model_key(model_dir)
        model_dir_path = self.get_model_directory_path(model_key, model_dir)

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
        return self._verify_files_workflow(files_to_check, model_dir_path)

    def _get_model_key(self, model_dir: Path) -> str:
        """Generate model key for data directory."""
        model_id = self.storage.generate_local_model_dir_name(model_dir)
        return f"local/{model_id}"

    def get_files_for_verification(self, model_dir: Path) -> list[dict[str, str]]:
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


def verify_local_model(model_dir: str | Path, gui=False, exit_on_reject=True) -> bool:
    """
    Check if the local model hash has changed and verify local files.

    Args:
        model_dir: Path to the local model directory
        gui: If True, launch GUI for verification if needed
        exit_on_reject: If True, exit the process when verification fails

    Returns:
        bool: True if verification successful or no changes detected
    """
    model_dir = Path(model_dir)

    # Check if the model directory exists
    if not model_dir.exists():
        print(f"Model directory {model_dir} does not exist.")
        if exit_on_reject:
            print(VERIFICATION_FAILED_MESSAGE)
            exit(1)
        return False

    target = TargetLocal()
    new_model_hash = target.detect_model_changes(model_dir)

    # If no changes detected, model is already verified
    if not new_model_hash:
        print("No changes detected in the model directory. Model is already verified.")
        return True

    # Handle verification based on mode
    if gui:
        result = target.handle_gui_verification(model_dir=model_dir)
    else:
        result = _handle_cli_verification(target, model_dir, new_model_hash)

    if not result and exit_on_reject:
        print(VERIFICATION_FAILED_MESSAGE)
        exit(1)

    return result


def _handle_cli_verification(
    target: TargetLocal, model_dir: Path, new_model_hash: str
) -> bool:
    """Handle CLI-based verification."""
    print("\n" + "=" * 50)
    print("Checking local Python files...")
    verified_all = target.verify_local_files(model_dir)
    print(f"File check result: {verified_all}")

    if verified_all:
        # Get directory and update hash
        model_key = target._get_model_key(model_dir)
        model_dir_path = target.get_model_directory_path(model_key, model_dir)
        target.update_model_hash(model_dir_path, new_model_hash)

        # Register in global registry
        target.register_model_in_registry(
            "local",
            target.storage.generate_local_model_dir_name(model_dir),
            str(model_dir),
        )

        print("Verified model hash updated.")
        return True
    else:
        return False
