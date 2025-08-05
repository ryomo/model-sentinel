"""
GUI components for Model Sentinel verification interface.
"""

from typing import Any, Dict, List

from model_sentinel.verify.verify import Verify

try:
    import gradio as gr
except ImportError:
    raise ImportError(
        "Gradio is required for GUI functionality. "
        "Install it with: pip install 'model-sentinel[gui]'"
    )

from .utils import format_status, STATUS_PENDING


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


def create_file_verification_interface(
    files_to_verify: List[Dict[str, Any]],
    verification_result: Dict[str, Any],
    gui_state: Dict[str, Any]
) -> List[gr.Checkbox]:
    """Create the file verification interface with blocking completion."""
    gr.Markdown("## � Files Requiring Verification")
    gr.Markdown("Please review the following files and approve if they are safe:")

    # Create checkboxes for each file and display content
    file_checkboxes = []

    for i, file_info in enumerate(files_to_verify):
        filename = file_info.get("filename", f"File {i+1}")
        content = file_info.get("content", "No content available")

        with gr.Row():
            with gr.Column(scale=1):
                checkbox = gr.Checkbox(
                    label=f"Approve {filename}",
                    value=False,
                    elem_id=f"checkbox_{i}"
                )
                file_checkboxes.append(checkbox)

        with gr.Row():
            with gr.Column():
                gr.Markdown(f"**File:** {filename}")
                if "hash" in file_info:
                    hash_short = file_info["hash"][:16] + "..."
                    gr.Markdown(f"**Hash:** `{hash_short}`")

                gr.Code(
                    value=content,
                    language="python",
                    label=f"Content of {filename}",
                    lines=10
                )
        gr.Markdown("---")

    # Final approval section
    create_final_verification_interface(
        verification_result, files_to_verify, file_checkboxes, gui_state
    )

    return file_checkboxes


def create_no_files_section(verification_result: Dict[str, Any]) -> None:
    """Create section when no files need verification."""
    if verification_result.get("files_verified"):
        gr.Markdown("## ✅ All Files Verified")
        gr.Markdown("No file changes detected or all files are already verified.")
    else:
        gr.Markdown("## ⚠️ Verification Issues")
        gr.Markdown("Some files could not be verified. Check the logs for details.")


def create_simple_interface() -> gr.Blocks:
    """Create simple interface when no model is specified."""
    with gr.Blocks(title="Model Sentinel") as demo:
        gr.Markdown("# 🛡️ Model Sentinel")
        gr.Markdown("Please specify a model to verify.")
        gr.Markdown("Use CLI: `model-sentinel --gui` or call with model parameters.")
    return demo


def create_file_verification_interface(
    files_to_verify: List[Dict[str, Any]],
    verification_result: Dict[str, Any],
    gui_state: Dict[str, Any]
) -> List[gr.Checkbox]:
    """Create the file verification interface with blocking completion."""
    gr.Markdown("## 📝 Files Requiring Verification")
    gr.Markdown("Please review the following files and approve if they are safe:")

    # Create checkboxes for each file and display content
    file_checkboxes = []

    for i, file_info in enumerate(files_to_verify):
        filename = file_info.get("filename", f"File {i+1}")
        content = file_info.get("content", "No content available")

        with gr.Row():
            with gr.Column(scale=1):
                checkbox = gr.Checkbox(
                    label=f"Approve {filename}",
                    value=False,
                    elem_id=f"checkbox_{i}"
                )
                file_checkboxes.append(checkbox)

        with gr.Row():
            with gr.Column():
                gr.Markdown(f"**File:** {filename}")
                if "hash" in file_info:
                    hash_short = file_info["hash"][:16] + "..."
                    gr.Markdown(f"**Hash:** `{hash_short}`")

                gr.Code(
                    value=content,
                    language="python",
                    label=f"Content of {filename}",
                    lines=10
                )
        gr.Markdown("---")

    # Final approval section
    create_final_verification_interface(
        verification_result, files_to_verify, file_checkboxes, gui_state
    )

    return file_checkboxes


def create_final_verification_interface(
    verification_result: Dict[str, Any],
    files_to_verify: List[Dict[str, Any]],
    file_checkboxes: List[gr.Checkbox],
    gui_state: Dict[str, Any]
) -> None:
    """Create final verification section with checkbox-based completion."""
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

    # HTML component for completion messages
    close_browser_html = gr.HTML(value="", visible=True)

    def complete_verification_simple(*checkbox_values):
        # Get list of approved files based on checkbox values
        approved_files = []
        total_files = len(files_to_verify)

        for i, is_approved in enumerate(checkbox_values):
            if is_approved and i < len(files_to_verify):
                filename = files_to_verify[i]["filename"]
                approved_files.append(filename)

        # Check if all files are approved
        if len(approved_files) == total_files and total_files > 0:
            # All files approved - save and return success
            verify = Verify()
            verify.save_verification_results(verification_result, approved_files)
            gui_state["verification_result"] = True

            # Display completion message to user
            close_script = """
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center; font-family: Arial, sans-serif;">
                <h3 style="margin: 0 0 10px 0;">🎉 Verification Complete!</h3>
                <p style="margin: 0; font-size: 16px;">All files have been successfully verified and saved.</p>
                <p style="margin: 10px 0 0 0; font-size: 14px; color: #6c757d;"><strong>The server will close automatically in a few seconds.</strong></p>
            </div>
            """

            # Set completion flag to trigger server shutdown
            gui_state["completion_requested"] = True

            return "✅ Verification completed successfully!", close_script

        else:
            # Not all files approved - show error and exit
            error_msg = f"❌ Not all files approved ({len(approved_files)}/{total_files}). Verification failed."
            gui_state["verification_result"] = False

            close_script = """
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center; font-family: Arial, sans-serif;">
                <h3 style="margin: 0 0 10px 0;">❌ Verification Failed</h3>
                <p style="margin: 0; font-size: 16px;">Not all files were approved. The verification process has been cancelled.</p>
                <p style="margin: 10px 0 0 0; font-size: 14px; color: #6c757d;"><strong>The server will close automatically in a few seconds.</strong></p>
            </div>
            """

            # Set completion flag to trigger server shutdown
            gui_state["completion_requested"] = True

            return error_msg, close_script

    final_approve_btn.click(
        complete_verification_simple,
        inputs=file_checkboxes,
        outputs=[final_status, close_browser_html]
    )
