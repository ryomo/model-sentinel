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
