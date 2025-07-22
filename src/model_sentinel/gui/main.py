"""
Main GUI interface for Model Sentinel.
"""

from typing import Any, Dict, List, Optional

try:
    import gradio as gr
except ImportError:
    raise ImportError(
        "Gradio is required for GUI functionality. "
        "Install it with: pip install 'model-sentinel[gui]'"
    )

from .components import (
    create_error_interface,
    create_no_files_section,
    create_simple_interface,
    create_verification_summary,
)
from .utils import GUI_PORT, GUI_URL
from .verification import get_verification_result


# Global variable to store verification result from GUI
_gui_verification_result = None


def launch_verification_gui(
    repo_id: str = None, model_dir: str = None, revision: str = "main"
) -> bool:
    """
    Launch GUI for model verification and wait for user interaction.

    Args:
        repo_id: Hugging Face repository ID (for HF models)
        model_dir: Local model directory path (for local models)
        revision: Model revision (for HF models)

    Returns:
        bool: True if verification successful and all files approved, False otherwise
    """
    global _gui_verification_result

    # Reset global state
    _gui_verification_result = None

    if repo_id:
        try:
            result = get_verification_result(repo_id)
            return _launch_gui_with_result(result, "Hugging Face")
        except Exception as e:
            print(f"Error accessing repository: {str(e)}")
            return False
    elif model_dir:
        try:
            result = get_verification_result(model_dir)
            return _launch_gui_with_result(result, "Local")
        except Exception as e:
            print(f"Error accessing model directory: {str(e)}")
            return False
    else:
        print("Error: Either repo_id or model_dir must be specified")
        return False


def _launch_gui_with_result(result: Dict[str, Any], model_type: str) -> bool:
    """Launch GUI with verification result and wait for completion."""
    files_to_verify = []
    if result.get("model_hash_changed") and result.get("files_info"):
        files_to_verify = result["files_info"]

    demo = create_verification_gui(result, files_to_verify)

    print(f"🚀 Launching {model_type} model verification GUI")
    print(GUI_URL)

    # Launch and wait for completion (blocking)
    demo.launch(
        share=False,
        inbrowser=True,
        server_name="127.0.0.1",
        server_port=GUI_PORT,
        prevent_thread_lock=False  # Make it blocking
    )

    # After GUI closes, return the result
    return _gui_verification_result if _gui_verification_result is not None else False


def create_verification_gui(
    verification_result: Dict[str, Any], files_to_verify: List[Dict[str, Any]] = None
) -> gr.Blocks:
    """Create GUI for verification with blocking behavior."""

    with gr.Blocks(title="Model Sentinel - Verification Results") as demo:
        gr.Markdown("# 🛡️ Model Sentinel - Verification Results")

        # Display verification summary
        with gr.Row():
            with gr.Column():
                create_verification_summary(verification_result)

        # File verification section
        if files_to_verify and len(files_to_verify) > 0:
            _create_file_verification_interface(files_to_verify, verification_result)
        else:
            create_no_files_section(verification_result)

    return demo


def _create_file_verification_interface(
    files_to_verify: List[Dict[str, Any]], verification_result: Dict[str, Any]
) -> None:
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
    _create_final_verification_section(
        verification_result, files_to_verify, file_checkboxes
    )


def _create_final_verification_section(
    verification_result: Dict[str, Any],
    files_to_verify: List[Dict[str, Any]],
    file_checkboxes: List[gr.Checkbox],
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
        global _gui_verification_result

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
            from .verification import save_verification_results

            save_verification_results(verification_result, approved_files)
            _gui_verification_result = True

            # Display completion message to user
            close_script = """
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center; font-family: Arial, sans-serif;">
                <h3 style="margin: 0 0 10px 0;">🎉 Verification Complete!</h3>
                <p style="margin: 0; font-size: 16px;">All files have been successfully verified and saved.</p>
                <p style="margin: 10px 0 0 0; font-size: 14px; color: #6c757d;"><strong>You can now close this browser tab.</strong></p>
            </div>
            """

            return "✅ Verification completed successfully!", close_script

        else:
            # Not all files approved - show error and exit
            error_msg = f"❌ Not all files approved ({len(approved_files)}/{total_files}). Verification failed."
            _gui_verification_result = False

            close_script = """
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center; font-family: Arial, sans-serif;">
                <h3 style="margin: 0 0 10px 0;">❌ Verification Failed</h3>
                <p style="margin: 0; font-size: 16px;">Not all files were approved. The verification process has been cancelled.</p>
                <p style="margin: 10px 0 0 0; font-size: 14px; color: #6c757d;"><strong>You can close this browser tab.</strong></p>
            </div>
            """

            return error_msg, close_script

    final_approve_btn.click(
        complete_verification_simple,
        inputs=file_checkboxes,
        outputs=[final_status, close_browser_html]
    )


def _show_error_gui(error_message: str):
    """Show a simple error GUI."""
    demo = create_error_interface(error_message)
    _launch_demo(demo, "Model Sentinel GUI (Error)")


def _launch_demo(demo: gr.Blocks, description: str):
    """Launch a Gradio demo."""
    print(f"🚀 Launching {description}")
    print(GUI_URL)

    demo.launch(
        share=False, inbrowser=True, server_name="127.0.0.1", server_port=GUI_PORT
    )


def _launch_gui_with_result(result: Dict[str, Any], model_type: str):
    """Launch GUI with verification result."""
    files_to_verify = []
    if result.get("model_hash_changed") and result.get("files_info"):
        files_to_verify = result["files_info"]

    demo = create_verification_gui(result, files_to_verify)
    _launch_demo(demo, f"Model Sentinel GUI for {model_type} model verification")


def _show_error_gui(error_message: str):
    """Show a simple error GUI."""
    demo = create_error_interface(error_message)
    _launch_demo(demo, "Model Sentinel GUI (Error)")


def _launch_demo(demo: gr.Blocks, description: str):
    """Launch a Gradio demo."""
    print(f"🚀 Launching {description}")
    print(GUI_URL)

    demo.launch(
        share=False, inbrowser=True, server_name="127.0.0.1", server_port=GUI_PORT
    )


def main():
    """Launch the Model Sentinel GUI application with command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Model Sentinel GUI")
    parser.add_argument(
        "--repo",
        type=str,
        help="Hugging Face repository ID (e.g., ryomo/malicious-code-test)",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default="main",
        help="Model revision/branch (default: main)",
    )
    parser.add_argument("--local", type=str, help="Path to local model directory")

    args = parser.parse_args()

    # Launch GUI with specified model
    if args.repo:
        launch_verification_gui(repo_id=args.repo, revision=args.revision)
    elif args.local:
        launch_verification_gui(model_dir=args.local)
    else:
        launch_verification_gui()


if __name__ == "__main__":
    main()
