# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.3.0] - 2025-08-05

### Feat

- feat: add version argument to CLI for displaying model-sentinel version
- feat: add GitHub Actions workflow for automated PyPI release process

### Refactor

- refactor: consolidate storage management and eliminate verification code duplication
- refactor: streamline file verification process and user prompt handling
- refactor: extract GUI business logic to Verify class

### Fix

- fix: remove hardcoded revision assignment in favor of parameter
- fix: unify exit behavior for GUI in `verify_hf_model()` and `verify_local_model()`
- Fix model-sentinel CLI test in release workflow
- Fix deprecated actions/upload-artifact and actions/download-artifact to v4

### Chore

- chore: bump version to v0.3.0
- chore: update unittest configuration in settings.json
- chore: simplify model verification process in inference script
- chore: update Python version compatibility to include 3.11 and 3.12
- chore: update commit message generation instructions for clarity
- chore: downgrade Python version requirement to 3.10 and update unittest accordingly
- chore: reorder CLI argument definitions for improved help output clarity
- chore: bump model-sentinel version to 0.2.0

### Docs

- docs: add publishing instructions for automatic PyPI deployment

## [0.2.0] - 2025-07-29

### Added

- Saving of Python script file copies for verification ([30cefa5](../../commit/30cefa5))
- Help command information to README ([e820f34](../../commit/e820f34))

### Changed

- Renamed "storage" module to "directory" for better clarity ([34def1e](../../commit/34def1e))
- Improved CLI behavior to show help when no model is specified ([f1e1a9b](../../commit/f1e1a9b))
- Updated README to clarify CLI usage ([e820f34](../../commit/e820f34))

### Fixed

- Removed default repository name from CLI ([f1e1a9b](../../commit/f1e1a9b))

## [0.1.0] - 2025-07-24

### Initial Release

- Initial release of model-sentinel
- CLI interface for security verification of AI model scripts
- GUI interface using Gradio
- Support for Hugging Face models verification
- Support for local model directory verification
- Hash-based file integrity checking
- JSON-based verification state management
- Cross-platform support (uvx executable)

### Security Features

- Detection of potentially malicious code in Python files
- Verification of file integrity using SHA-256 hashes
- Safe handling of model file analysis

[0.2.0]: ../../compare/v0.1.0...v0.2.0
[0.1.0]: ../../releases/tag/v0.1.0
