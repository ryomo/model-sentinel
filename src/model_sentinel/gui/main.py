"""
Main GUI interface for Model Sentinel.
"""

from typing import Any, Dict, List

try:
    import gradio as gr
except ImportError:
    raise ImportError(
        "Gradio is required for GUI functionality. "
        "Install it with: pip install 'model-sentinel[gui]'"
    )

from .components import (
    create_error_interface,
    create_file_list_section,
    create_file_preview_section,
    create_final_verification_section,
    create_no_files_section,
    create_simple_interface,
    create_verification_summary,
)
from .handlers import FileApprovalState, setup_file_selection_handlers
from .utils import GUI_PORT, GUI_URL
from .verification import get_verification_result


def create_verification_gui(
    verification_result: Dict[str, Any], files_to_verify: List[Dict[str, Any]] = None
) -> gr.Blocks:
    """
    Create GUI for displaying verification results and file approval.

    Args:
        verification_result: Result from verify_hf_model or verify_local_model
        files_to_verify: List of files that need user approval

    Returns:
        Gradio Blocks interface
    """

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


def launch_verification_gui(
    repo_id: str = None, model_dir: str = None, revision: str = "main"
):
    """
    Launch GUI for model verification.

    Args:
        repo_id: Hugging Face repository ID (for HF models)
        model_dir: Local model directory path (for local models)
        revision: Model revision (for HF models) - Note: Currently uses 'main' by default
    """

    if repo_id:
        try:
            # Note: revision parameter is handled internally by target layer
            result = get_verification_result(repo_id)
            _launch_gui_with_result(result, "Hugging Face")
        except Exception as e:
            _show_error_gui(f"Error accessing repository: {str(e)}")
    elif model_dir:
        try:
            result = get_verification_result(model_dir)
            _launch_gui_with_result(result, "Local")
        except Exception as e:
            _show_error_gui(f"Error accessing model directory: {str(e)}")
    else:
        # No model specified - show simple interface
        demo = create_simple_interface()
        _launch_demo(demo, "Model Sentinel GUI")


def launch_verification_gui_unified(target_spec: str):
    """
    Launch GUI for model verification with unified interface.

    Args:
        target_spec: Model specification (repo_id for HF, path for local)
    """
    try:
        result = get_verification_result(target_spec)
        model_type = "Hugging Face" if result.get("target_type") == "hf" else "Local"
        _launch_gui_with_result(result, model_type)
    except Exception as e:
        _show_error_gui(f"Error accessing model: {str(e)}")
def _create_file_verification_interface(
    files_to_verify: List[Dict[str, Any]], verification_result: Dict[str, Any]
) -> None:
    """Create the file verification interface."""
    gr.Markdown("## 📝 Files Requiring Verification")
    gr.Markdown("Please review the following files and approve if they are safe:")

    # Create file approval state manager
    file_approval_state = FileApprovalState(files_to_verify)

    # Create main layout with left file list and right content area
    with gr.Row():
        # Left column: File list
        with gr.Column(scale=1, min_width=300):
            file_buttons = create_file_list_section(files_to_verify)

        # Right column: Content preview and approval controls
        with gr.Column(scale=3):
            (
                selected_file_md,
                file_content,
                approval_controls,
                file_hash_display,
                current_approval_status,
                approve_btn,
                reject_btn,
            ) = create_file_preview_section()

    # Hidden state to track currently selected file
    selected_file_index = gr.Number(value=-1, visible=False)

    # Set up all event handlers
    setup_file_selection_handlers(
        file_approval_state,
        file_buttons,
        selected_file_md,
        file_content,
        approval_controls,
        file_hash_display,
        current_approval_status,
        selected_file_index,
        approve_btn,
        reject_btn,
    )

    # Final approval section
    create_final_verification_section(
        verification_result, file_approval_state.get_approval_components()
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
