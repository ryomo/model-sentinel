# Model Sentinel Metadata Schema v1

## Minimal example

```json
{
  "schema_version": 1,
  "run": {
    "run_id": "...",
    "timestamp": "2025-08-12T10:45:12.345Z",
    "tool_version": "1.2.3",
    "target": { "type": "hf", "id": "org/model@main" }
  },
  "model_hash": "abc123...",
  "last_verified": "2025-08-12T10:45:12.345Z",
  "overall_status": "ok",
  "approved_files": [
    { "path": "README.md", "size": 1024, "hash": "...", "verified_at": "2025-08-12T10:45:12.345Z" }
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
    - `size`: string|null,
    - `hash`: string|null,
    - `verified_at`: string|null

## Rules

- Timestamps: Use ISO 8601 with timezone; prefer UTC (Z or +00:00).
