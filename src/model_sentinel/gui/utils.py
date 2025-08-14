"""
Constants and utility functions for Model Sentinel GUI.
"""

import difflib

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
    new_model_hash: str, files_info: list[dict[str, str]], display_info: list[str]
) -> dict:
    """Prepare verification result data for GUI flow.

    Args:
        new_model_hash: New model hash to compare against
        files_info: List of file dictionaries with filename, content, and hash
        display_info: Information to display in result

    Returns:
        Verification result dictionary
    """

    result = {
        "status": "success",
        "model_hash_changed": bool(new_model_hash),
        "new_model_hash": new_model_hash,
        "files_verified": False,
        "message": f"Found {len(files_info)} files that need verification.",
        "files_info": files_info,
        "display_info": display_info,
    }

    return result
