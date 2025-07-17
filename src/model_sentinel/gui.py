"""
Model Sentinel GUI Application using Gradio.

This module provides a web-based graphical user interface for the Model Sentinel
verification functionality. The GUI shows verification results and allows users
to approve file changes.
"""

import difflib
from typing import Any, Dict, List

try:
    import gradio as gr
except ImportError:
    raise ImportError(
        "Gradio is required for GUI functionality. "
        "Install it with: pip install 'model-sentinel[gui]'"
    )

from model_sentinel.verify.verify import Verify

# Status constants to avoid duplication
STATUS_SUCCESS = "✅ Success"
STATUS_FAILED = "⚠️ Failed"
STATUS_ERROR = "❌ Error"
STATUS_PENDING = "🔄 Pending"


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
                _create_verification_summary(verification_result)

        # File verification section
        if files_to_verify and len(files_to_verify) > 0:
            _create_file_verification_section(files_to_verify, verification_result)
        else:
            _create_no_files_section(verification_result)

    return demo


def _format_status(status: str) -> str:
    """Format status for display."""
    status_icons = {
        "success": STATUS_SUCCESS,
        "failed": STATUS_FAILED,
        "error": STATUS_ERROR,
        "pending": STATUS_PENDING,
    }
    return status_icons.get(status, f"❓ {status}")


def _generate_diff_html(old_content: str, new_content: str, filename: str) -> str:
    """Generate HTML diff between two file contents."""
    differ = difflib.HtmlDiff()
    return differ.make_file(
        old_content.splitlines(),
        new_content.splitlines(),
        f"{filename} (old)",
        f"{filename} (new)",
    )


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
        if "repo_id" in verification_result:
            # HF model
            repo_id = verification_result["repo_id"]
            revision = verification_result.get("revision")
            model_key = f"hf/{repo_id}@{revision}" if revision else f"hf/{repo_id}"
        elif "model_dir" in verification_result:
            # Local model
            model_dir = verification_result["model_dir"]
            model_key = f"local/{model_dir}"
        else:
            return "❌ Error: Unable to determine model type"

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
        files_info = verification_result.get("files_info", [])
        approved_count = 0

        for file_info in files_info:
            filename = file_info.get("filename", "")
            file_hash = file_info.get("hash", "")

            if filename in approved_files and file_hash:
                data[model_key]["files"][filename] = file_hash
                approved_count += 1
                print(f"✅ Approved file: {filename} - {file_hash[:16]}...")

        # Save to file
        verify.save_verified_hashes(data)
        print("💾 Saved verification data to hash file")

        return f"✅ Verification completed! {approved_count} files approved and saved."

    except Exception as e:
        error_msg = f"❌ Error saving verification results: {str(e)}"
        print(error_msg)
        return error_msg


# GUI constants
GUI_URL = "📍 URL: http://127.0.0.1:7862"
GUI_PORT = 7862


def _get_hf_verification_result(repo_id: str, revision: str) -> dict:
    """Get verification result for HF model."""
    from model_sentinel.target.hf import TargetHF

    target = TargetHF()
    new_model_hash = target.detect_model_changes(repo_id, revision)

    result = {
        "repo_id": repo_id,
        "revision": revision,
        "status": "success",
        "model_hash_changed": bool(new_model_hash),
        "new_model_hash": new_model_hash,
        "files_verified": False,
        "message": "",
        "files_info": [],
    }

    if not new_model_hash:
        result["message"] = "No changes detected in the model hash."
        result["files_verified"] = True
    else:
        files_info = target.get_files_for_verification(repo_id, revision)
        result["files_info"] = files_info
        result["message"] = f"Found {len(files_info)} files that need verification."

    return result


def _get_local_verification_result(model_dir: str) -> dict:
    """Get verification result for local model."""
    from pathlib import Path

    from model_sentinel.target.local import TargetLocal

    model_path = Path(model_dir)
    if not model_path.exists():
        raise FileNotFoundError(f"Model directory {model_dir} does not exist.")

    target = TargetLocal()
    new_model_hash = target.detect_model_changes(model_path)

    result = {
        "model_dir": str(model_path),
        "status": "success",
        "model_hash_changed": bool(new_model_hash),
        "new_model_hash": new_model_hash,
        "files_verified": False,
        "message": "",
        "files_info": [],
    }

    if not new_model_hash:
        result["message"] = "No changes detected in the model directory."
        result["files_verified"] = True
    else:
        files_info = target.get_files_for_verification(model_path)
        result["files_info"] = files_info
        result["message"] = f"Found {len(files_info)} files that need verification."

    return result


def _launch_gui_with_result(result: dict, model_type: str):
    """Launch GUI with verification result."""
    files_to_verify = []
    if result.get("model_hash_changed") and result.get("files_info"):
        files_to_verify = result["files_info"]

    demo = create_verification_gui(result, files_to_verify)

    print(f"🚀 Launching Model Sentinel GUI for {model_type} model verification")
    print(GUI_URL)

    demo.launch(
        share=False, inbrowser=True, server_name="127.0.0.1", server_port=GUI_PORT
    )


def launch_verification_gui(
    repo_id: str = None, model_dir: str = None, revision: str = "main"
):
    """
    Launch GUI for model verification.

    Args:
        repo_id: Hugging Face repository ID (for HF models)
        model_dir: Local model directory path (for local models)
        revision: Model revision (for HF models)
    """

    if repo_id:
        try:
            result = _get_hf_verification_result(repo_id, revision)
            _launch_gui_with_result(result, "Hugging Face")
        except Exception as e:
            _show_error_gui(f"Error accessing repository: {str(e)}")
    elif model_dir:
        try:
            result = _get_local_verification_result(model_dir)
            _launch_gui_with_result(result, "Local")
        except Exception as e:
            _show_error_gui(f"Error accessing model directory: {str(e)}")
    else:
        # No model specified - show simple interface
        with gr.Blocks(title="Model Sentinel") as demo:
            gr.Markdown("# 🛡️ Model Sentinel")
            gr.Markdown("Please specify a model to verify.")
            gr.Markdown(
                "Use CLI: `model-sentinel --gui` or call with model parameters."
            )

        print("🚀 Launching Model Sentinel GUI")
        print(GUI_URL)

        demo.launch(
            share=False, inbrowser=True, server_name="127.0.0.1", server_port=GUI_PORT
        )


def _show_error_gui(error_message: str):
    """Show a simple error GUI."""
    with gr.Blocks(title="Model Sentinel - Error") as demo:
        gr.Markdown("# 🛡️ Model Sentinel - Error")
        gr.Markdown(f"❌ **Error:** {error_message}")

    print("🚀 Launching Model Sentinel GUI (Error)")
    print(GUI_URL)

    demo.launch(
        share=False, inbrowser=True, server_name="127.0.0.1", server_port=GUI_PORT
    )



def _create_verification_summary(verification_result: Dict[str, Any]) -> None:
    """Create the verification summary section."""
    gr.Markdown("## 📋 Verification Summary")

    # Basic info
    if "repo_id" in verification_result:
        gr.Markdown(f"**Repository:** {verification_result['repo_id']}")
        if verification_result.get("revision"):
            gr.Markdown(f"**Revision:** {verification_result['revision']}")
    elif "model_dir" in verification_result:
        gr.Markdown(f"**Model Directory:** {verification_result['model_dir']}")

    # Status
    status = _format_status(verification_result.get("status", "unknown"))
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


def _create_file_selection_handlers(
    files_to_verify: List[Dict[str, Any]],
    file_approval_components: List[Dict[str, Any]],
    file_buttons: List[gr.Button],
    selected_file_md: gr.Markdown,
    file_content: gr.Code,
    approval_controls: gr.Row,
    file_hash_display: gr.Markdown,
    current_approval_status: gr.Textbox,
    selected_file_index: gr.Number,
    approve_btn: gr.Button,
    reject_btn: gr.Button
):
    """Set up file selection and approval handlers."""

    def select_file(file_index):
        """Handle file selection."""
        if file_index < 0 or file_index >= len(files_to_verify):
            return (
                "*Select a file from the left to preview*",
                "",
                gr.update(visible=False),
                gr.update(visible=False),
                "",
                STATUS_PENDING,
                file_index
            )

        file_info = files_to_verify[file_index]
        filename = file_info.get("filename", f"File {file_index+1}")
        content = file_info.get("content", "No content available")

        # File info markdown
        file_md = f"**File:** {filename}"
        if "hash" in file_info:
            hash_short = file_info["hash"][:16] + "..."
            file_hash_md = f"**Hash:** `{hash_short}`"
        else:
            file_hash_md = "**Hash:** Not available"

        # Get current approval status
        current_status = file_approval_components[file_index]["approval_status"].value or STATUS_PENDING

        return (
            file_md,
            content,
            gr.update(visible=True),
            gr.update(visible=True),
            file_hash_md,
            current_status,
            file_index
        )

    def approve_current_file(selected_index):
        """Approve currently selected file."""
        if 0 <= selected_index < len(file_approval_components):
            file_approval_components[selected_index]["approval_state"].value = 1
            return STATUS_SUCCESS
        return STATUS_PENDING

    def reject_current_file(selected_index):
        """Reject currently selected file."""
        if 0 <= selected_index < len(file_approval_components):
            file_approval_components[selected_index]["approval_state"].value = -1
            return STATUS_FAILED
        return STATUS_PENDING

    # Set up file button click handlers
    for i, btn in enumerate(file_buttons):
        btn.click(
            lambda idx=i: select_file(idx),
            outputs=[
                selected_file_md,
                file_content,
                file_content,
                approval_controls,
                file_hash_display,
                current_approval_status,
                selected_file_index
            ]
        )

    # Set up approval button handlers
    approve_btn.click(
        approve_current_file,
        inputs=[selected_file_index],
        outputs=[current_approval_status]
    )

    reject_btn.click(
        reject_current_file,
        inputs=[selected_file_index],
        outputs=[current_approval_status]
    )


def _create_file_verification_section(
    files_to_verify: List[Dict[str, Any]], verification_result: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Create the file verification section with left file list and right content preview."""
    gr.Markdown("## 📝 Files Requiring Verification")
    gr.Markdown("Please review the following files and approve if they are safe:")

    # Create state variables for each file
    file_approval_components = []

    # Create main layout with left file list and right content area
    with gr.Row():
        # Left column: File list
        with gr.Column(scale=1, min_width=300):
            gr.Markdown("### 📁 Files to Review")

            # File selection buttons
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

                # Create approval state for this file
                approval_state = gr.Number(
                    value=0, visible=False, elem_id=f"state_{i}"
                )
                approval_status = gr.Textbox(
                    value=STATUS_PENDING,
                    visible=False,
                    elem_id=f"status_{i}",
                )

                file_approval_components.append({
                    "filename": filename,
                    "approval_state": approval_state,
                    "approval_status": approval_status,
                    "file_info": file_info
                })

        # Right column: Content preview and approval controls
        with gr.Column(scale=3):
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

    # Hidden state to track currently selected file
    selected_file_index = gr.Number(value=-1, visible=False)

    # Set up all event handlers
    _create_file_selection_handlers(
        files_to_verify,
        file_approval_components,
        file_buttons,
        selected_file_md,
        file_content,
        approval_controls,
        file_hash_display,
        current_approval_status,
        selected_file_index,
        approve_btn,
        reject_btn
    )

    # Final approval section
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

        final_approve_btn.click(
            complete_verification,
            outputs=[final_status]
        )

    return file_approval_components


def _create_no_files_section(verification_result: Dict[str, Any]) -> None:
    """Create section when no files need verification."""
    if verification_result.get("files_verified"):
        gr.Markdown("## ✅ All Files Verified")
        gr.Markdown("No file changes detected or all files are already verified.")
    else:
        gr.Markdown("## ⚠️ Verification Issues")
        gr.Markdown("Some files could not be verified. Check the logs for details.")


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
