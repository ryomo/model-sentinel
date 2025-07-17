"""
Verification logic for Model Sentinel GUI.
"""

from typing import Any, Dict, List, Union
from pathlib import Path

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
    Save verification results to hash file.

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
        data = verify.load_verified_hashes()

        # Determine model key
        model_key = verify.get_model_key_from_result(verification_result)
        print(f"🔑 Model key: {model_key}")

        # Initialize model data if not exists
        if model_key not in data:
            data[model_key] = {"model_hash": None, "files": {}}

        # Update model hash
        if verification_result.get("new_model_hash"):
            data[model_key]["model_hash"] = verification_result["new_model_hash"]
            print(
                f"🔄 Updated model hash: {verification_result['new_model_hash'][:16]}..."
            )

        # Update file hashes for approved files
        approved_count = _update_approved_files(
            data[model_key], verification_result, approved_files
        )

        # Save to file
        verify.save_verified_hashes(data)
        print("💾 Saved verification data to hash file")

        return f"✅ Verification completed! {approved_count} files approved and saved."

    except Exception as e:
        error_msg = f"❌ Error saving verification results: {str(e)}"
        print(error_msg)
        return error_msg


def _update_approved_files(
    model_data: Dict[str, Any],
    verification_result: Dict[str, Any],
    approved_files: List[str],
) -> int:
    """Update file hashes for approved files."""
    files_info = verification_result.get("files_info", [])
    approved_count = 0

    for file_info in files_info:
        filename = file_info.get("filename", "")
        file_hash = file_info.get("hash", "")

        if filename in approved_files and file_hash:
            model_data["files"][filename] = file_hash
            approved_count += 1
            print(f"✅ Approved file: {filename} - {file_hash[:16]}...")

    return approved_count
