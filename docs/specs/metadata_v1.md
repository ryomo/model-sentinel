# Model Sentinel Metadata Schema v1

## Directory

Verification data is stored in a structured `.model-sentinel/` directory.

```file
.model-sentinel/
├── registry.json           # Global registry of verified models
├── local/                  # Local models
│   └── {model_name}_{hash}/   # Short hash of directory content ("*.py")
│       ├── metadata.json   # Model metadata and file info
│       ├── original_path.txt # Original model directory path (for local models)
│       └── files/          # Individual file content
└── hf/                     # HuggingFace models
    └── {org}/{model}@{revision}/
        ├── metadata.json
        └── files/
```

## `metadata.json` example

```json
{
  "schema_version": 1,
  "run": {
    "run_id": "...",
    "timestamp": "2025-08-12T10:45:12.345Z",
    "tool_version": "0.3.0",
    "target": {"type": "hf", "id": "org/model@main"}
  },
  "model_hash": "abc123...",
  "last_verified": "2025-08-12T10:45:12.345Z",
  "overall_status": "ok",
  "approved_files": [
    {
      "path": "modeling.py",
      "hash": "def456...",
      "size": 1024,
      "verified_at": "2025-08-12T10:45:12.345Z"
    }
  ]
}
```

## Fields

- `schema_version`: number (must be 1)
- `run`:
  - `run_id`: string|null,
  - `timestamp`: ISO 8601,
  - `tool_version`: string,
  - `target`:
    - `type`: "hf"|"local"|"unknown",
    - `id`: string
- `model_hash`: string|null
- `last_verified`: ISO 8601 string|null
- `overall_status`: one of "ok" | "ng" (If ng_count == 0 → "ok", else → "ng")
- `approved_files`: array of FileRecord (approved files only)
  - FileRecord:
    - `path`,
    - `hash`: string|null,
    - `size`: number|null,
    - `verified_at`: string|null

## Notes

- Timestamps: Use ISO 8601 with timezone; prefer UTC (Z or +00:00).
