# AI Assistant Instructions

## General Guidelines

- Always use context7 to look up library or API documentation when needed.
- NEVER run git commands or commit changes.
  - However, when appropriate, suggest recommended git commands or commit messages in the chat, but do not execute them. The user will handle all git operations.
  - Always write commit messages in English.
- Inform the user when background processes are running and should be manually terminated.
- Delete temporary debug scripts and other temporary artifacts after development tasks. (e.g., `debug_*.py`)

## Coding Best Practices

- Follow modern best practices for code style, readability, and maintainability.
- Prefer code consistency and clear naming conventions.
- When creating new files, always reference existing file names in the same directory or similar contexts to follow consistent naming conventions.
  - Example: When creating test files, check existing test file names to ensure consistency (e.g., `test_module.py` for testing `module.py`)
  - Maintain consistent patterns across the entire project structure

### Python

- **Use `pathlib` for path and file operations instead of `os.path` or `glob`.**
  - Example: `from pathlib import Path` # Not `import os.path`
- Use type annotations, f-strings, comprehensions, and other modern Python features whenever possible.

#### Testing

- When implementing new classes or functions, create corresponding test files in the `tests/` directory
- **Use `unittest` framework for all testing - DO NOT use `pytest`.**
- Follow the existing test structure in the `tests/` directory
- Follow existing test file naming conventions (e.g., `test_module.py` for testing `module.py`)
- Aim for comprehensive test coverage including both positive and negative test cases
- Ensure tests are isolated and do not depend on external resources
  - Use `unittest.mock` for mocking dependencies in tests

## File Structure

### Operation when changing file structure

If there are any changes to the file structure, be sure to record and update them in this section.

### Current file structure

The main directories and files of the project are as follows (items excluded by .gitignore are omitted):

```file
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
  - tests/
    - test_cli.py: Tests for CLI functionality
    - test_target/: Tests for target implementations
    - test_verify/: Tests for verification functionality
    - data/: Test sample data and configurations
```

## Agent Task Documentation Guidelines

- For any user instruction that is the first directive in the current context and is not a simple question or a single-step task, create a new file under `docs/agent/` in the format `YYYYMMDD_{serial}.md` (serial should be a two-digit number, e.g., 01, 02, ...).
  - After creating this documentation file, you MUST confirm with the user that the plan and approach are acceptable before proceeding with ANY implementation work.
  - DO NOT start implementation, make technology choices, or proceed with coding until the user explicitly approves the documentation.
- In this file, clearly describe the situation and break down what needs to be done into concrete steps. For complex tasks, divide the work into multiple actionable steps.
- Update and edit this file as needed throughout the task to reflect progress, changes, or additional information.
- The documentation file should be written in the language used by the user.
