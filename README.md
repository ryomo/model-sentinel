# 🛡️ Model Sentinel

A security verification tool for model scripts - Detects and verifies changes in Python files of AI models.

## Features

- **Hugging Face Hub Model Verification**: Detect changes in Python files of remote models
- **Local Model Verification**: Detect changes in model files in local directories
- **Hash-based Verification**: Verify file integrity using hashes
- **Interactive Approval**: Review and approve content of changed files
- **GUI Support**: Intuitive web-based GUI interface

## Installation

### Basic Version (CLI only)

```bash
pip install model-sentinel
```

### GUI Version

```bash
pip install "model-sentinel[gui]"
```

### Development Environment (uv)

```bash
# Clone repository
git clone https://github.com/ryomo/model-sentinel.git
cd model-sentinel

# Install dependencies
uv sync

# Test GUI version
uv run python -m model_sentinel.gui
```

## Usage

### CLI Usage

```bash
# Verify specified Hugging Face model
model-sentinel --repo ryomo/malicious-code-test

# Verify local model
model-sentinel --local ./my-model-directory

# Specify revision
model-sentinel --repo ryomo/malicious-code-test --revision v1.0

# Launch GUI (with model specified)
model-sentinel --gui --repo ryomo/malicious-code-test

# Launch GUI (with local model)
model-sentinel --gui --local ./my-model-directory

# Other options
model-sentinel --list-verified
model-sentinel --delete
```

### Python Script Usage

```python
from model_sentinel import verify_hf_model, verify_local_model

# Verify Hugging Face model
result = verify_hf_model("ryomo/malicious-code-test")

# Verify local model
result = verify_local_model("./my-model-directory")

# Verify with GUI mode
result = verify_hf_model("ryomo/malicious-code-test", gui=True)
```

### GUI Usage

1. **Launch GUI**:

    ```bash # Launch GUI with specified model
    model-sentinel --gui --repo ryomo/malicious-code-test

    # Launch GUI with local model
    model-sentinel --gui --local ./my-model-directory

    # Launch GUI without model specification (can specify later)
    model-sentinel --gui

    # Or run directly as Python module
    python -m model_sentinel.gui --repo ryomo/malicious-code-test
    ```

2. **Verification Process**:

    - Verification of specified model runs automatically
    - If changed files are found, review content in GUI
    - Click approve button if deemed safe
    - Verification results are saved to hash file

3. **Practical Usage Example (verification before script execution)**:

    ```python
    # scripts/your_inference.py
    from model_sentinel import verify_hf_model   def main():
        REPO_NAME = "ryomo/malicious-code-test"

        # Verify before script execution (GUI version)
        if not verify_hf_model(REPO_NAME, gui=True):
            print("Model verification failed!")
            return

        # Use model safely after verification
        model = AutoModelForCausalLM.from_pretrained(REPO_NAME)
        # ...
    ```

## Verification Process

1. **Hash Comparison**: Calculate hash of entire model or directory and compare with previous verification
2. **File Verification**: If changes detected, check individual Python files
3. **Content Display**: Show content of changed files (pager in CLI, web interface in GUI)
4. **User Approval**: Only approve if user confirms content is trustworthy
5. **Hash Update**: Save hash of approved files to `.model-sentinel.json`

## Configuration File

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

## Technical Specifications

- **Python**: 3.12+
- **Package Manager**: uv
- **GUI Framework**: Gradio 5.x
- **Hash Algorithm**: SHA-256
- **Supported Files**: Python files (.py)

## Development

```bash
# Setup development environment
uv sync

# Run tests
uv run python -m pytest

# Run GUI development
uv run python -m model_sentinel.gui --repo ryomo/malicious-code-test

# Run CLI development
uv run model-sentinel --help
```

## License

[License Information]

## Contributing

Pull requests and issue reports are welcome.
