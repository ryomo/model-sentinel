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
    create_file_verification_interface,
    create_no_files_section,
    create_simple_interface,
    create_verification_summary,
)
from .utils import GUI_PORT, GUI_URL
from .verification import get_verification_result


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
        demo = create_simple_interface()
        demo.launch(
            share=False, inbrowser=True, server_name="127.0.0.1", server_port=GUI_PORT
        )
        return False


def _launch_gui_with_result(result: Dict[str, Any], model_type: str) -> bool:
    """Launch GUI with verification result and wait for completion."""
    import threading
    import time

    # Initialize GUI state
    gui_state = {
        "verification_result": None,
        "completion_requested": False
    }

    files_to_verify = []
    if result.get("model_hash_changed") and result.get("files_info"):
        files_to_verify = result["files_info"]

    demo = create_verification_gui(result, files_to_verify, gui_state)

    print(f"🚀 Launching {model_type} model verification GUI")
    print(GUI_URL)

    # If no files to verify (already verified), auto-close after short display
    if not files_to_verify:
        demo.launch(
            share=False,
            inbrowser=True,
            server_name="127.0.0.1",
            server_port=GUI_PORT,
            prevent_thread_lock=True
        )
        print("No files to verify. Displaying result for 5 seconds...")
        time.sleep(5)
        demo.close()
        print("✅ GUI display completed. Server closed.")
        return True

    def monitor_completion():
        """Monitor completion flag and shutdown server"""
        while not gui_state["completion_requested"]:
            time.sleep(0.5)  # Check every 0.5 seconds

        # Wait a bit to show completion message, then shutdown
        time.sleep(2)

        print("🔄 Closing Gradio server...")
        gr.close_all()
        print("✅ Gradio server closed.")

    # Launch demo
    demo.launch(
        share=False,
        inbrowser=True,
        server_name="127.0.0.1",
        server_port=GUI_PORT,
        prevent_thread_lock=True
    )

    # Start background completion monitoring
    monitor_thread = threading.Thread(target=monitor_completion, daemon=True)
    monitor_thread.start()

    # Wait for completion in main thread
    while not gui_state["completion_requested"]:
        time.sleep(0.1)

    # Wait for monitor thread to finish
    monitor_thread.join(timeout=5)

    # Return the verification result
    return gui_state["verification_result"] if gui_state["verification_result"] is not None else False


def create_verification_gui(
    verification_result: Dict[str, Any],
    files_to_verify: List[Dict[str, Any]] = None,
    gui_state: Dict[str, Any] = None
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
            create_file_verification_interface(files_to_verify, verification_result, gui_state)
        else:
            create_no_files_section(verification_result)

    return demo
