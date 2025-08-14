"""
Constants and utility functions for Model Sentinel GUI.
"""

import difflib
from typing import Any

# Status constants
STATUS_SUCCESS = "✅ Success"
STATUS_FAILED = "⚠️ Failed"
STATUS_ERROR = "❌ Error"
STATUS_PENDING = "🔄 Pending"


def format_status(status: str) -> str:
    """Format status for display."""
    status_icons = {
        "success": STATUS_SUCCESS,
        "failed": STATUS_FAILED,
        "error": STATUS_ERROR,
        "pending": STATUS_PENDING,
    }
    return status_icons.get(status, f"❓ {status}")


def generate_diff_html(old_content: str, new_content: str, filename: str) -> str:
    """
    Generate HTML diff between two file contents.
    TODO: This function is not used for now, but can be used in future for displaying diffs in the GUI.
    """
    differ = difflib.HtmlDiff()
    return differ.make_file(
        old_content.splitlines(),
        new_content.splitlines(),
        f"{filename} (old)",
        f"{filename} (new)",
    )


def prepare_gui_verification_result(
    target: Any, detect_args: tuple, verify_args: tuple, display_info: list[str]
) -> dict:
    """Prepare verification result data for GUI flow.

    Args:
        target: Target instance (HF or Local)
        detect_args: Arguments for detect_model_changes (as tuple)
        verify_args: Arguments for get_files_for_verification (as tuple)
        display_info: Information to display in result

    Returns:
        Verification result dictionary
    """
    new_model_hash = target.detect_model_changes(*detect_args)

    result = {
        "status": "success",
        "model_hash_changed": bool(new_model_hash),
        "new_model_hash": new_model_hash,
        "files_verified": False,
        "message": "",
        "files_info": [],
        "display_info": display_info,
    }

    if not new_model_hash:
        result["message"] = "No changes detected in the model hash."
        result["files_verified"] = True
    else:
        files_info = target.get_files_for_verification(*verify_args)
        result["files_info"] = files_info
        result["message"] = f"Found {len(files_info)} files that need verification."

    return result
