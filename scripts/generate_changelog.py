"""
Generate a simple CHANGELOG entry for a given tag by inspecting git commits
between the previous tag and the given tag. The script prepends a markdown
section to CHANGELOG.md and exits 0. It is designed to run inside CI where
git and Python are available.

Usage:
  python scripts/generate_changelog.py <tag>

Notes:
  - The script will look for the previous tag by creatordate order. If none
    found, it will include all commits.
  - Commit messages are grouped by conventional prefix (feat, fix, docs, chore,
    refactor, test, perf, ci) when present. Other messages go into "other".
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

# Commits whose subject contains this token will be excluded from CHANGELOG
SKIP_TOKEN = "[skip changelog]"


def run(cmd: List[str], cwd: Optional[Path] = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd).decode("utf-8").strip()


def get_previous_tag(current_tag: str) -> Optional[str]:
    # Return the tag immediately older than current_tag (by creatordate).
    tags = run(["git", "tag", "--sort=creatordate"]).splitlines()
    if current_tag not in tags:
        return None
    idx = tags.index(current_tag)
    if idx == 0:
        return None
    return tags[idx - 1]


def get_commits(from_ref: Optional[str], to_ref: str) -> List[str]:
    range_expr = f"{from_ref}..{to_ref}" if from_ref else to_ref
    try:
        out = run(["git", "log", "--pretty=format:%s", range_expr])
    except subprocess.CalledProcessError:
        return []
    if not out:
        return []
    # Filter out commits explicitly marked to skip changelog updates
    return [line for line in out.splitlines() if SKIP_TOKEN not in line]


def classify(commits: List[str]) -> dict:
    groups = defaultdict(list)
    for msg in commits:
        lower = msg.lower()
        for prefix in (
            "feat:",
            "refactor:",
            "fix:",
            "perf:",
            "test:",
            "ci:",
            "chore:",
            "docs:",
        ):
            if lower.startswith(prefix):
                groups[prefix.rstrip(":")].append(msg)
                break
        else:
            groups["other"].append(msg)
    return groups


def format_section(tag: str, groups: dict) -> str:
    # date may be filled by caller; default to today
    date = datetime.date.today().isoformat()
    lines = [f"## [{tag}] - {date}", ""]
    for key in (
        "feat",
        "refactor",
        "fix",
        "perf",
        "test",
        "ci",
        "chore",
        "docs",
        "other",
    ):
        items = groups.get(key)
        if not items:
            continue
        header = key.capitalize() if key != "other" else "Other"
        lines.append(f"### {header}")
        lines.append("")
        for m in items:
            lines.append(f"- {m}")
        lines.append("")
    return "\n".join(lines)


def prepend_changelog(new_section: str, changelog_path: Path) -> None:
    # Deprecated: kept for compatibility
    if not changelog_path.exists():
        changelog_path.write_text("# Changelog\n\n")
    original = changelog_path.read_text()
    content = new_section + "\n" + original
    changelog_path.write_text(content)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: generate_changelog.py <tag>")
        return 2
    tag = sys.argv[1]
    changelog = Path("CHANGELOG.md")

    prev = get_previous_tag(tag)
    commits = get_commits(prev, tag)
    if not commits:
        print("No commits found for this range; no CHANGELOG changes.")
        return 0

    groups = classify(commits)
    section = format_section(tag, groups)
    prepend_changelog(section, changelog)
    print(f"Wrote CHANGELOG.md with {sum(len(v) for v in groups.values())} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
