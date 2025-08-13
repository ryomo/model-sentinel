# 🛡️ Model Sentinel

A security verification tool for model scripts - Detects and verifies changes in Python files of AI models.

## Features

- **Hugging Face Hub Model Verification**: Detect changes in Python files of remote models
- **Local Model Verification**: Detect changes in model files in local directories
- **Hash-based Verification**: Verify file integrity using hashes
- **Interactive Approval**: Review and approve content of changed files
- **GUI Support**: Intuitive web-based GUI interface

## Quickstart

Get started in seconds:

```bash
pip install "model-sentinel[gui]"
```

Embed verification in your Python script (Hugging Face model example):

```python
from model_sentinel import verify_hf_model

# Launches interactive verification (GUI if gui=True) and exits on rejection for safety.
verify_hf_model("ryomo/malicious-code-test", gui=True)
```

## Installation

### Basic Version (CLI only)

```bash
pip install model-sentinel
```

### GUI Version

```bash
pip install "model-sentinel[gui]"
```

## Usage

### CLI Usage

```bash
# Show help and usage instructions
model-sentinel

# Verify Hugging Face model
model-sentinel --hf ryomo/malicious-code-test
model-sentinel --hf ryomo/malicious-code-test --revision main  # optional revision

# Verify local model
model-sentinel --local ./my-model-directory

# List all verified models
model-sentinel --list-verified

# Delete all verification data
model-sentinel --delete
```

### GUI Usage

*Note: GUI commands require the GUI version to be installed.*

```bash
model-sentinel --gui --hf ryomo/malicious-code-test
model-sentinel --gui --local ./my-model-directory
```

### Python Script Usage

```python
from model_sentinel import verify_hf_model, verify_local_model

# Verify Hugging Face model
verify_hf_model("ryomo/malicious-code-test")

# Verify local model
verify_local_model("./my-model-directory")

# Verify with GUI mode
verify_hf_model("ryomo/malicious-code-test", gui=True)  # GUI window will open

# Receive boolean result without exiting on rejection
result = verify_hf_model("ryomo/malicious-code-test", exit_on_reject=False)
if result:
    print("Model verified. Proceeding...")
else:
    print("Verification failed or was rejected.")
```

## Verification Process

1. **Hash Comparison**: Calculate hash of entire model or directory and compare with previous verification
2. **File Verification**: If changes detected, check individual Python files
3. **Content Display**: Show content of changed files (pager in CLI, web interface in GUI)
4. **User Approval**: Only approve if user confirms content is trustworthy
5. **Directory Update**: Save file content and metadata to `.model-sentinel/` directory structure

## Verification Data Directory

Verification data is stored in a structured `.model-sentinel/` directory:

```file
.model-sentinel/
├── registry.json           # Global registry of verified models
├── local/                  # Local models
│   └── {model_name}_{content_hash8}/   # Short hash of directory content ("*.py") for portability
│       ├── metadata.json   # Model metadata and file info
│       ├── original_path.txt # Original model directory path (for local models)
│       └── files/          # Individual file content
└── hf/                     # HuggingFace models
    └── {org}/{model}@{revision}/
        ├── metadata.json
        └── files/
```

Example `metadata.json`:

```json
{
  "schema_version": 1,
  "run": {
    "run_id": "...",
    "timestamp": "2025-07-28T10:30:00Z",
    "tool_version": "0.3.0",
    "target": {"type": "hf", "id": "org/model@main"}
  },
  "model_hash": "abc123...",
  "last_verified": "2025-07-28T10:30:00Z",
  "overall_status": "ok",
  "approved_files": [
    {
      "path": "modeling.py",
      "hash": "def456...",
      "size": 1024,
      "verified_at": "2025-07-28T10:30:00Z"
    }
  ]
}
```

## Development

For development and contributing to this project:

```bash
# Clone and setup
git clone https://github.com/ryomo/model-sentinel.git
cd model-sentinel

# Install dependencies
uv sync

# Run from source (for testing)
uv run model-sentinel  # Show help
uv run model-sentinel --hf ryomo/malicious-code-test
uv run model-sentinel --local ./my-model-directory
uv run model-sentinel --gui --hf ryomo/malicious-code-test
```

## Testing

This project uses Python's built-in `unittest` for testing.

### Running Tests

Run all tests:

```bash
uv run python -m unittest discover tests -v
```

Run specific test module:

```bash
uv run python -m unittest tests.test_verify.test_verify -v
uv run python -m unittest tests.test_target.test_base -v
uv run python -m unittest tests.test_cli -v
```

### Test Coverage

Generate coverage reports:

```bash
# Run tests with coverage
uv run python -m coverage run -m unittest discover tests

# Generate coverage report
uv run python -m coverage report --include="src/*"

# Generate HTML coverage report
uv run python -m coverage html --include="src/*"
# Open htmlcov/index.html in browser
```

## Publishing

This project uses GitHub Actions to automatically publish to PyPI when a new version tag is pushed.

**Steps:**

1. Run `uv run python scripts/bump_version.py 1.2.3` (replace `1.2.3` with the new version number).

    The script will automatically update the version number in the following files:
    - `pyproject.toml`
    - `src/model_sentinel/__init__.py`

2. Follow the recommended commands shown in the output like below.

    ```sh
    uv sync
    git add pyproject.toml src/model_sentinel/__init__.py uv.lock
    git commit -m "chore: bump version to v1.2.3"
    git push
    git tag v1.2.3
    git push origin v1.2.3
    ```

GitHub Actions will build and publish the package to PyPI automatically.

## Technical Specifications

- **Python**: 3.10, 3.11, 3.12+
- **Package Manager**: uv
- **GUI Framework**: Gradio 5.x
- **Hash Algorithm**: SHA-256
- **Supported Files**: Python files (.py)

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Pull requests and issue reports are welcome.
