"""
Constants and utility functions for Model Sentinel GUI.
"""

import difflib

# Status constants
STATUS_SUCCESS = "✅ Success"
STATUS_FAILED = "⚠️ Failed"
STATUS_ERROR = "❌ Error"
STATUS_PENDING = "🔄 Pending"

# GUI constants
GUI_URL = "📍 URL: http://127.0.0.1:7862"
GUI_PORT = 7862


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
    """Generate HTML diff between two file contents."""
    differ = difflib.HtmlDiff()
    return differ.make_file(
        old_content.splitlines(),
        new_content.splitlines(),
        f"{filename} (old)",
        f"{filename} (new)",
    )
