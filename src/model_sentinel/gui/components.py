"""
GUI components for Model Sentinel verification interface.
"""

from typing import Any, Dict, List

try:
    import gradio as gr
except ImportError:
    raise ImportError(
        "Gradio is required for GUI functionality. "
        "Install it with: pip install 'model-sentinel[gui]'"
    )

from .utils import format_status, STATUS_PENDING
from .verification import save_verification_results


def create_verification_summary(verification_result: Dict[str, Any]) -> None:
    """Create the verification summary section."""
    gr.Markdown("## 📋 Verification Summary")

    # Display target information (provided by verify layer)
    display_info = verification_result.get("display_info", [])
    for info in display_info:
        gr.Markdown(info)

    # Status
    status = format_status(verification_result.get("status", "unknown"))
    gr.Markdown(f"**Status:** {status}")
    gr.Markdown(f"**Message:** {verification_result.get('message', 'No message')}")

    # Hash info
    if verification_result.get("model_hash_changed"):
        gr.Markdown("**Model Hash:** 🔄 Changed")
        if verification_result.get("new_model_hash"):
            hash_short = verification_result["new_model_hash"][:16] + "..."
            gr.Markdown(f"**New Hash:** `{hash_short}`")
    else:
        gr.Markdown("**Model Hash:** ✅ Unchanged")


def create_file_list_section(files_to_verify: List[Dict[str, Any]]) -> List[gr.Button]:
    """Create file list buttons for file selection."""
    gr.Markdown("### 📁 Files to Review")

    file_buttons = []
    for i, file_info in enumerate(files_to_verify):
        filename = file_info.get("filename", f"File {i+1}")
        btn = gr.Button(
            f"📄 {filename}",
            variant="secondary",
            elem_id=f"file_btn_{i}",
            size="sm"
        )
        file_buttons.append(btn)

    return file_buttons


def create_file_preview_section() -> tuple:
    """Create file preview and approval controls section."""
    gr.Markdown("### 📋 File Preview")

    # Selected file info
    selected_file_md = gr.Markdown("*Select a file from the left to preview*")

    # File content display
    file_content = gr.Code(
        value="",
        language="python",
        label="File Content",
        lines=20,
        max_lines=30,
        visible=False
    )

    # File approval controls
    with gr.Row(visible=False) as approval_controls:
        with gr.Column(scale=2):
            # File info display
            file_hash_display = gr.Markdown("")

        with gr.Column(scale=1):
            # Approval buttons
            approve_btn = gr.Button(
                "✅ Approve & Trust",
                variant="primary",
            )
            reject_btn = gr.Button(
                "❌ Reject",
                variant="secondary",
            )

            current_approval_status = gr.Textbox(
                value=STATUS_PENDING,
                label="Status",
                interactive=False,
            )

    return (
        selected_file_md,
        file_content,
        approval_controls,
        file_hash_display,
        current_approval_status,
        approve_btn,
        reject_btn,
    )


def create_final_verification_section(
    verification_result: Dict[str, Any],
    file_approval_components: List[Dict[str, Any]],
) -> tuple:
    """Create final verification section with complete button."""
    gr.Markdown("## 🚀 Final Verification")

    with gr.Row():
        final_approve_btn = gr.Button(
            "🛡️ Complete Verification", variant="primary", size="lg"
        )
        final_status = gr.Textbox(
            value="Review files above and click to complete verification",
            label="Verification Status",
            interactive=False,
        )

    def complete_verification():
        # Get list of approved files based on state values
        approved_files = []
        for comp in file_approval_components:
            state_value = comp["approval_state"].value
            if state_value == 1:  # Approved
                filename = comp["filename"]
                approved_files.append(filename)

        if not approved_files:
            return "⚠️ No files approved. Please approve at least one file to save verification results."

        # Save verification results for approved files only
        result = save_verification_results(verification_result, approved_files)
        return result

    final_approve_btn.click(complete_verification, outputs=[final_status])

    return final_approve_btn, final_status


def create_no_files_section(verification_result: Dict[str, Any]) -> None:
    """Create section when no files need verification."""
    if verification_result.get("files_verified"):
        gr.Markdown("## ✅ All Files Verified")
        gr.Markdown("No file changes detected or all files are already verified.")
    else:
        gr.Markdown("## ⚠️ Verification Issues")
        gr.Markdown("Some files could not be verified. Check the logs for details.")


def create_error_interface(error_message: str) -> gr.Blocks:
    """Create error interface."""
    with gr.Blocks(title="Model Sentinel - Error") as demo:
        gr.Markdown("# 🛡️ Model Sentinel - Error")
        gr.Markdown(f"❌ **Error:** {error_message}")
    return demo


def create_simple_interface() -> gr.Blocks:
    """Create simple interface when no model is specified."""
    with gr.Blocks(title="Model Sentinel") as demo:
        gr.Markdown("# 🛡️ Model Sentinel")
        gr.Markdown("Please specify a model to verify.")
        gr.Markdown("Use CLI: `model-sentinel --gui` or call with model parameters.")
    return demo
