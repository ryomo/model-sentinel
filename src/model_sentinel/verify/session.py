from __future__ import annotations

from typing import Any, Iterable


def build_session_files(
    files_info: list[dict[str, Any]],
    approved_files: Iterable[str],
) -> list[dict[str, Any]]:
    """Build session records from files_info and approved filenames.

    Args:
        files_info: Items containing at least {"filename", "hash", "content"}
        approved_files: Iterable of approved filenames

    Returns:
        List of session dicts: {"filename", "hash", "content", "approved"}
    """

    approved_set = set(approved_files)
    session: list[dict[str, Any]] = []

    for fi in files_info:
        fname = fi.get("filename", "")
        session.append(
            {
                "filename": fname,
                "hash": fi.get("hash", ""),
                "content": fi.get("content", ""),
                "approved": fname in approved_set,
            }
        )

    return session
