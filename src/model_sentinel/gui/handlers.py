"""
Event handlers for Model Sentinel GUI.
"""

from typing import Any, Dict, List

try:
    import gradio as gr
except ImportError:
    raise ImportError(
        "Gradio is required for GUI functionality. "
        "Install it with: pip install 'model-sentinel[gui]'"
    )

from .utils import STATUS_SUCCESS, STATUS_FAILED, STATUS_PENDING


class FileApprovalState:
    """Manages file approval state and components."""

    def __init__(self, files_to_verify: List[Dict[str, Any]]):
        self.files_to_verify = files_to_verify
        self.approval_components = self._create_approval_components()

    def _create_approval_components(self) -> List[Dict[str, Any]]:
        """Create approval state components for each file."""
        components = []
        for i, file_info in enumerate(self.files_to_verify):
            filename = file_info.get("filename", f"File {i+1}")

            approval_state = gr.Number(
                value=0, visible=False, elem_id=f"state_{i}"
            )
            approval_status = gr.Textbox(
                value=STATUS_PENDING,
                visible=False,
                elem_id=f"status_{i}",
            )

            components.append({
                "filename": filename,
                "approval_state": approval_state,
                "approval_status": approval_status,
                "file_info": file_info
            })

        return components

    def get_approval_components(self) -> List[Dict[str, Any]]:
        """Get the approval components list."""
        return self.approval_components


def setup_file_selection_handlers(
    file_approval_state: FileApprovalState,
    file_buttons: List[gr.Button],
    selected_file_md: gr.Markdown,
    file_content: gr.Code,
    approval_controls: gr.Row,
    file_hash_display: gr.Markdown,
    current_approval_status: gr.Textbox,
    selected_file_index: gr.Number,
    approve_btn: gr.Button,
    reject_btn: gr.Button,
):
    """Set up file selection and approval handlers."""

    def select_file(file_index):
        """Handle file selection."""
        files_to_verify = file_approval_state.files_to_verify
        file_approval_components = file_approval_state.get_approval_components()

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
        current_status = (
            file_approval_components[file_index]["approval_status"].value
            or STATUS_PENDING
        )

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
        file_approval_components = file_approval_state.get_approval_components()
        if 0 <= selected_index < len(file_approval_components):
            file_approval_components[selected_index]["approval_state"].value = 1
            return STATUS_SUCCESS
        return STATUS_PENDING

    def reject_current_file(selected_index):
        """Reject currently selected file."""
        file_approval_components = file_approval_state.get_approval_components()
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
