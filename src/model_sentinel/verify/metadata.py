from __future__ import annotations

from typing import Any, TypedDict, Literal, Iterable

# ------------------
# Type Definitions
# ------------------

class SessionFile(TypedDict, total=False):
    filename: str
    hash: str
    content: str
    approved: bool


class FileRecord(TypedDict, total=False):
    path: str
    size: int | None
    hash: str | None
    status: Literal["ok", "ng", "skipped", "unknown"]
    verified_at: str | None


class RunInfoTarget(TypedDict, total=False):
    type: str
    id: str


class RunInfo(TypedDict, total=False):
    run_id: str | None
    timestamp: str
    tool_version: str
    target: RunInfoTarget


class Summary(TypedDict, total=False):
    total: int
    ok: int
    ng: int
    skipped: int
    unknown: int


class MetadataPayload(TypedDict, total=False):
    schema_version: int
    run: RunInfo
    model_hash: str | None
    last_verified: str | None
    overall_status: str
    summary: Summary
    files: list[FileRecord]


def approved_map_from_existing(existing_files: Any) -> dict[str, dict[str, Any]]:
    """Build approved file map from existing metadata files entry (legacy dict or new list).

    Pure function: no I/O.
    """
    approved_map: dict[str, dict[str, Any]] = {}
    if isinstance(existing_files, dict):
        for k, v in existing_files.items():
            approved_map[k] = {
                "hash": v.get("hash"),
                "size": v.get("size"),
                "verified_at": v.get("verified_at"),
            }
    elif isinstance(existing_files, list):
        for item in existing_files:
            if item.get("status", "ok") == "ok":
                approved_map[item.get("path", "")] = {
                    "hash": item.get("hash"),
                    "size": item.get("size"),
                    "verified_at": item.get("verified_at"),
                }
    return approved_map


def files_list_from_map(approved_map: dict[str, dict[str, Any]]) -> list[FileRecord]:
    """Convert approved file map to the new list-based files entry.

    Pure function: no I/O.
    """
    files_list: list[dict[str, Any]] = []
    for path in sorted(approved_map.keys()):
        rec = approved_map[path]
        files_list.append(
            {
                "path": path,
                "size": rec.get("size"),
                "hash": rec.get("hash"),
                "status": "ok",
                "verified_at": rec.get("verified_at"),
            }
        )
    return files_list


def build_summary_and_overall(total: int, ok_count: int, ng_count: int) -> tuple[Summary, str]:
    """Build summary dict and overall status string.

    Pure function: no I/O.
    """
    summary = {
        "total": total,
        "ok": ok_count,
        "ng": ng_count,
        "skipped": 0,
        "unknown": 0,
    }
    if ng_count == 0:
        overall = "ok"
    elif ok_count == 0:
        overall = "ng"
    else:
        overall = "mixed"
    return summary, overall


def compute_run_metadata(
    existing_metadata: dict[str, Any],
    session_files: list[SessionFile],
    *,
    target_type: str,
    target_id: str,
    tool_version: str,
    timestamp_iso: str,
    current_timestamp: str,
) -> MetadataPayload:
    """Compute new metadata.json content from inputs.

    Pure function: receives timestamps and produces a dict. No I/O.
    """
    existing_files = existing_metadata.get("files")
    approved_map = approved_map_from_existing(existing_files)

    ok_count = 0
    ng_count = 0
    total = len(session_files)

    for sf in session_files:
        if sf.get("approved"):
            ok_count += 1
            fname = sf.get("filename", "")
            content = sf.get("content", "")
            approved_map[fname] = {
                "hash": sf.get("hash", ""),
                "size": len(str(content).encode("utf-8")),
                "verified_at": current_timestamp,
            }
        else:
            ng_count += 1

    files_list = files_list_from_map(approved_map)
    summary, overall = build_summary_and_overall(total, ok_count, ng_count)

    new_meta: MetadataPayload = {
        "schema_version": 1,
        "run": {
            "run_id": None,  # Optional: can be filled by caller if needed
            "timestamp": timestamp_iso,
            "tool_version": tool_version,
            "target": {"type": target_type, "id": target_id},
        },
        "model_hash": existing_metadata.get("model_hash"),
        "last_verified": existing_metadata.get("last_verified"),
        "overall_status": overall,
        "summary": summary,
        "files": files_list,
    }

    return new_meta


# ------------------
# Validation Helpers (lightweight)
# ------------------
from model_sentinel.verify.errors import ValidationError

def validate_session_files(session_files: Iterable[SessionFile]) -> None:
    seen: set[str] = set()
    for idx, sf in enumerate(session_files):
        fname = sf.get("filename")
        if not fname:
            raise ValidationError(f"Session file at index {idx} missing 'filename'.")
        if fname in seen:
            raise ValidationError(f"Duplicate session filename detected: {fname}")
        seen.add(fname)
        if "approved" in sf and not isinstance(sf["approved"], bool):
            raise ValidationError(f"'approved' must be bool for {fname}")

def validate_metadata_payload(meta: MetadataPayload) -> None:
    if meta.get("schema_version") != 1:
        raise ValidationError("Unsupported schema_version (expected 1).")
    run = meta.get("run") or {}
    if not run.get("timestamp"):
        raise ValidationError("Run timestamp missing.")
    if not isinstance(meta.get("files"), list):
        raise ValidationError("'files' must be a list.")
    summary = meta.get("summary") or {}
    for key in ("total", "ok", "ng"):
        if key not in summary:
            raise ValidationError(f"Summary missing '{key}'.")
