"""
bump_version.py

Usage:
    python scripts/bump_version.py <new_version>
        or
    uv run python scripts/bump_version.py <new_version>

Updates the version in pyproject.toml and src/model_sentinel/__init__.py.
After updating, prints recommended commands for commit and tag.
"""

import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print("Usage: python scripts/bump_version.py <new_version>")
    sys.exit(1)

new_version = sys.argv[1]


def update_version_in_file(file_path: Path, pattern: str, new_version: str) -> None:
    """Update version in a file using regex pattern.

    Args:
        file_path: Path to the file to update
        pattern: Regex pattern to match the version string
        new_version: New version string to replace with
    """
    text = file_path.read_text(encoding="utf-8")
    text_new = re.sub(pattern, new_version, text, flags=re.MULTILINE)
    file_path.write_text(text_new, encoding="utf-8")
    print(f"Updated {file_path} to version {new_version}")


# Update pyproject.toml
update_version_in_file(
    Path("pyproject.toml"), r'(?<=^version = ")([^"]+)(?=")', new_version
)

# Update __init__.py
update_version_in_file(
    Path("src/model_sentinel/__init__.py"),
    r'(?<=^__version__ = ")([^"]+)(?=")',
    new_version,
)

# Print recommended git commands
print(
    """
Recommended commands:
    uv sync
    git add pyproject.toml src/model_sentinel/__init__.py uv.lock
    git commit -m \"chore: bump version to v{new_version}\"
    git push
    git tag v{new_version}
    git push origin v{new_version}
""".format(new_version=new_version)
)
