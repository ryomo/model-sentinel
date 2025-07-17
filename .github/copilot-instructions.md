## AI Assistant Instructions

- **Always use context7 to look up library or API documentation when needed.**
- **NEVER run git commands or commit changes.**
  - However, when appropriate, suggest recommended git commands or commit messages in the chat, but do not execute them. The user will handle all git operations.
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
