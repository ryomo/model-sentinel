## AI Assistant Instructions

- **Always use context7 to look up library or API documentation when needed.**
- **NEVER run git commands or commit changes.**
  - However, when appropriate, suggest recommended git commands or commit messages in the chat, but do not execute them. The user will handle all git operations.
  - Always write commit messages in English.
- **Terminal Management:**
  - Always inform the user when background processes are running and should be manually terminated.
- **Cleanup:**
  - Delete temporary debug scripts, test files, and other temporary artifacts after development tasks. (e.g., `debug_*.py`, `test_*.py`)

### Coding Best Practices
- Follow modern best practices for code style, readability, and maintainability.
- Prefer code consistency and clear naming conventions.

#### Python
- **Use `pathlib` for path and file operations instead of `os.path` or `glob`.**
  - Example: `from pathlib import Path`  # Not `import os.path`
- Use type annotations, f-strings, comprehensions, and other modern Python features whenever possible.

## File Structure

### Operation when changing file structure

If there are any changes to the file structure, be sure to record and update them in this section.

### Current file structure

The main directories and files of the project are as follows (items excluded by .gitignore are omitted):

- Project root
  - LICENSE
  - pyproject.toml
  - README.md
  - uv.lock
  - docs/
  - scripts/
    - inference_from_hub.py
  - src/
    - model_sentinel/
      - __init__.py
      - cli.py: Command-line interface for Model Sentinel.
      - gui/
        - __init__.py
        - components.py: Contains Gradio components for the GUI.
        - handlers.py: Contains event handlers for the Model Sentinel GUI.
        - main.py: Main entry point for the GUI.
        - utils.py: Provides constants and utility functions for the GUI.
        - verification.py: Implements verification logic for models in the GUI.
      - target/
        - __init__.py
        - base.py: Base class for all target implementations.
        - hf.py: Target class for tracking Hugging Face model changes.
        - local.py: Target class for tracking local model changes.
      - verify/
        - __init__.py
        - verify.py: Base class for verifying model changes and file integrity.
