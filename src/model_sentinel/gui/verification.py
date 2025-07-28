"""
Verification logic for Model Sentinel GUI.
"""

from typing import Any, Dict, List, Union
from pathlib import Path
from datetime import datetime

from model_sentinel.verify.verify import Verify


def get_verification_result(target_spec: Union[str, Path]) -> Dict[str, Any]:
    """
    Get verification result for any model type (unified interface).

    Args:
        target_spec: Model specification (repo_id for HF, path for local)

    Returns:
        Unified verification result dictionary
    """
    verify = Verify()
    return verify.get_unified_verification_result(str(target_spec))


def save_verification_results(
    verification_result: Dict[str, Any], approved_files: List[str]
) -> str:
    """
    Save verification results using the directory system.

    Args:
        verification_result: Original verification result
        approved_files: List of approved filenames

    Returns:
        Status message
    """
    if not verification_result.get("model_hash_changed"):
        return "No changes to save."

    try:
        print(
            f"🔍 Saving verification results for {len(approved_files)} approved files: {approved_files}"
        )

        verify = Verify()

        # Determine model key and get directory
        model_key = verify.get_model_key_from_result(verification_result)
        print(f"🔑 Model key: {model_key}")

        # Get model directory
        if verification_result.get("target_type") == "local":
            model_path = Path(verification_result["model_dir"])
            model_dir = verify.directory_manager.get_local_model_dir(model_path)
        else:
            repo_id = verification_result["repo_id"]
            revision = verification_result.get("revision", "main")
            model_dir = verify.directory_manager.get_hf_model_dir(repo_id, revision)

        # Update model hash if changed
        if verification_result.get("new_model_hash"):
            verify.update_model_hash(model_dir, verification_result["new_model_hash"])
            print(f"🔄 Updated model hash: {verification_result['new_model_hash'][:16]}...")

        # Update file hashes for approved files using directory system
        approved_count = _update_approved_files_directory(
            model_dir, verification_result, approved_files, verify
        )

        # Register model in registry
        model_type, model_id = model_key.split('/', 1)
        kwargs = {}
        if verification_result.get("target_type") == "local":
            kwargs["original_path"] = verification_result["model_dir"]
        verify.directory_manager.register_model(model_type, model_id, **kwargs)

        print("💾 Saved verification data to directory system")
        return f"✅ Verification completed! {approved_count} files approved and saved."

    except Exception as e:
        error_msg = f"❌ Error saving verification results: {str(e)}"
        print(error_msg)
        return error_msg


def _update_approved_files_directory(
    model_dir: Path,
    verification_result: Dict[str, Any],
    approved_files: List[str],
    verify: Verify
) -> int:
    """Update file hashes for approved files using directory system."""
    files_info = verification_result.get("files_info", [])
    approved_count = 0

    for file_info in files_info:
        filename = file_info.get("filename", "")
        file_hash = file_info.get("hash", "")
        content = file_info.get("content", "")

        if filename in approved_files and file_hash:
            # Save file content and update metadata
            verify.directory_manager.save_file_content(model_dir, filename, content)

            # Update metadata
            metadata = verify.directory_manager.load_metadata(model_dir)
            metadata["files"][filename] = {
                "hash": file_hash,
                "size": len(content.encode('utf-8')),
                "verified_at": datetime.now().isoformat()
            }
            metadata["last_verified"] = datetime.now().isoformat()
            verify.directory_manager.save_metadata(model_dir, metadata)

            approved_count += 1
            print(f"✅ Approved file: {filename} - {file_hash[:16]}...")

    return approved_count
