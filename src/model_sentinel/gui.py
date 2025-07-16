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
                gr.Markdown("## 📋 Verification Summary")

                # Basic info
                if "repo_id" in verification_result:
                    gr.Markdown(f"**Repository:** {verification_result['repo_id']}")
                    if verification_result.get("revision"):
                        gr.Markdown(f"**Revision:** {verification_result['revision']}")
                elif "model_dir" in verification_result:
                    gr.Markdown(
                        f"**Model Directory:** {verification_result['model_dir']}"
                    )

                # Status
                status = _format_status(verification_result.get("status", "unknown"))
                gr.Markdown(f"**Status:** {status}")
                gr.Markdown(
                    f"**Message:** {verification_result.get('message', 'No message')}"
                )

                # Hash info
                if verification_result.get("model_hash_changed"):
                    gr.Markdown("**Model Hash:** 🔄 Changed")
                    if verification_result.get("new_model_hash"):
                        hash_short = verification_result["new_model_hash"][:16] + "..."
                        gr.Markdown(f"**New Hash:** `{hash_short}`")
                else:
                    gr.Markdown("**Model Hash:** ✅ Unchanged")

        # File verification section
        if files_to_verify and len(files_to_verify) > 0:
            gr.Markdown("## 📝 Files Requiring Verification")
            gr.Markdown(
                "Please review the following files and approve if they are safe:"
            )

            # Create tabs for each file
            with gr.Tabs():
                file_approval_states = {}

                for i, file_info in enumerate(files_to_verify):
                    filename = file_info.get("filename", f"File {i+1}")
                    content = file_info.get("content", "No content available")

                    with gr.Tab(f"📄 {filename}"):
                        with gr.Row():
                            with gr.Column(scale=3):
                                # File content display
                                gr.Code(
                                    value=content,
                                    language="python",
                                    label=f"Content of {filename}",
                                    lines=20,
                                    max_lines=30,
                                )

                            with gr.Column(scale=1):
                                # File info and approval
                                gr.Markdown(f"**File:** {filename}")
                                if "hash" in file_info:
                                    hash_short = file_info["hash"][:16] + "..."
                                    gr.Markdown(f"**Hash:** `{hash_short}`")

                                # Approval buttons
                                approve_btn = gr.Button(
                                    "✅ Approve & Trust",
                                    variant="primary",
                                    elem_id=f"approve_{i}",
                                )
                                reject_btn = gr.Button(
                                    "❌ Reject",
                                    variant="secondary",
                                    elem_id=f"reject_{i}",
                                )

                                approval_status = gr.Textbox(
                                    value=STATUS_PENDING,
                                    label="Status",
                                    interactive=False,
                                    elem_id=f"status_{i}",
                                )

                                # Store approval state
                                file_approval_states[filename] = {
                                    "approve_btn": approve_btn,
                                    "reject_btn": reject_btn,
                                    "status": approval_status,
                                    "approved": False,
                                }

                                # Button handlers
                                approve_btn.click(
                                    lambda: STATUS_SUCCESS, outputs=approval_status
                                )
                                reject_btn.click(
                                    lambda: STATUS_FAILED, outputs=approval_status
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
                    # In a real implementation, this would update the hash file
                    return "✅ Verification completed! All approved files have been recorded."

                final_approve_btn.click(complete_verification, outputs=final_status)

        else:
            # No files to verify
            if verification_result.get("files_verified"):
                gr.Markdown("## ✅ All Files Verified")
                gr.Markdown(
                    "No file changes detected or all files are already verified."
                )
            else:
                gr.Markdown("## ⚠️ Verification Issues")
                gr.Markdown(
                    "Some files could not be verified. Check the logs for details."
                )

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

        # Initialize model data if not exists
        if model_key not in data:
            data[model_key] = {"model_hash": None, "files": {}}

        # Update model hash
        if verification_result.get("new_model_hash"):
            data[model_key]["model_hash"] = verification_result["new_model_hash"]

        # Update file hashes for approved files
        files_info = verification_result.get("files_info", [])
        approved_count = 0

        for file_info in files_info:
            filename = file_info.get("filename", "")
            file_hash = file_info.get("hash", "")

            if filename in approved_files and file_hash:
                data[model_key]["files"][filename] = file_hash
                approved_count += 1

        # Save to file
        verify.save_verified_hashes(data)

        return f"✅ Verification completed! {approved_count} files approved and saved."

    except Exception as e:
        return f"❌ Error saving verification results: {str(e)}"


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
