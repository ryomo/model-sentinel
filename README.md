# 🛡️ Model Sentinel

A security verification tool for model scripts - Detects and verifies changes in Python files of AI models.

## Features

- **Hugging Face Hub Model Verification**: Detect changes in Python files of remote models
- **Local Model Verification**: Detect changes in model files in local directories
- **Hash-based Verification**: Verify file integrity using hashes
- **Interactive Approval**: Review and approve content of changed files
- **GUI Support**: Intuitive web-based GUI interface

## Installation

Basic Version (CLI only)

```bash
pip install model-sentinel
```

GUI Version

```bash
pip install "model-sentinel[gui]"
```

## Usage

### CLI Usage

```bash
model-sentinel --repo ryomo/malicious-code-test
model-sentinel --local ./my-model-directory
model-sentinel --gui --repo ryomo/malicious-code-test
```

### GUI Usage

*Note: GUI commands require the GUI version to be installed.*

```bash
model-sentinel --gui --repo ryomo/malicious-code-test
model-sentinel --gui --local ./my-model-directory
model-sentinel --gui
```

### Python Script Usage

```python
from model_sentinel import verify_hf_model, verify_local_model

# Verify Hugging Face model
result = verify_hf_model("ryomo/malicious-code-test")  # Returns True if verified, False otherwise

# Verify local model
result = verify_local_model("./my-model-directory")  # Returns True if verified, False otherwise

# Verify with GUI mode
result = verify_hf_model("ryomo/malicious-code-test", gui=True)  # GUI window will open
```

## Verification Process

1. **Hash Comparison**: Calculate hash of entire model or directory and compare with previous verification
2. **File Verification**: If changes detected, check individual Python files
3. **Content Display**: Show content of changed files (pager in CLI, web interface in GUI)
4. **User Approval**: Only approve if user confirms content is trustworthy
5. **Hash Update**: Save hash of approved files to `.model-sentinel.json`

## Verification Record

Verified hashes are saved in `.model-sentinel.json`:

```json
{
  "hf/ryomo/malicious-code-test@main": {
    "revision": "main",
    "model_hash": "abc123...",
    "files": {
      "modeling.py": "def456...",
      "configuration.py": "ghi789..."
    }
  }
}
```

## Development

```bash
# Clone repository
git clone https://github.com/ryomo/model-sentinel.git
cd model-sentinel

# Install dependencies
uv sync

# Usage in CLI
uv run model-sentinel --repo ryomo/malicious-code-test
uv run model-sentinel --local ./my-model-directory
uv run model-sentinel --gui --repo ryomo/malicious-code-test
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

## Technical Specifications

- **Python**: 3.12+
- **Package Manager**: uv
- **GUI Framework**: Gradio 5.x
- **Hash Algorithm**: SHA-256
- **Supported Files**: Python files (.py)

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Pull requests and issue reports are welcome.
