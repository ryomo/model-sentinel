"""Storage manager for Model Sentinel verification data."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class StorageManager:
    """Manages .model-sentinel directory structure and data persistence."""

    def __init__(self, base_dir: Path = Path(".model-sentinel")):
        """Initialize storage manager.

        Args:
            base_dir: Base directory for Model Sentinel data directory
        """
        self.base_dir = Path(base_dir)
        self.registry_file = self.base_dir / "registry.json"
        self.hf_dir = self.base_dir / "hf"
        self.local_dir = self.base_dir / "local"

    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format.

        Returns:
            Current timestamp as ISO 8601 string
        """
        return datetime.now().isoformat()

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.base_dir.mkdir(exist_ok=True)
        self.hf_dir.mkdir(exist_ok=True)
        self.local_dir.mkdir(exist_ok=True)

    def generate_local_model_dir_name(self, model_path: Path) -> str:
        """Generate directory name for local models using hybrid approach.

        Args:
            model_path: Path to the local model directory

        Returns:
            Directory name in format: {model_name}_{path_hash}
        """
        # Get readable model name
        readable_name = model_path.name

        # Generate path hash for uniqueness
        path_hash = hashlib.sha256(str(model_path).encode()).hexdigest()[:8]

        return f"{readable_name}_{path_hash}"

    def get_local_model_dir(self, model_path: Path) -> Path:
        """Get directory path for local model.

        Args:
            model_path: Path to the local model directory

        Returns:
            Path to directory for this model
        """
        dir_name = self.generate_local_model_dir_name(model_path)
        return self.local_dir / dir_name

    def get_hf_model_dir(self, repo_id: str, revision: str = "main") -> Path:
        """Get directory path for HuggingFace model.

        Args:
            repo_id: HuggingFace repository ID (e.g., "microsoft/DialoGPT-medium")
            revision: Model revision/branch

        Returns:
            Path to directory for this model
        """
        # Split repo_id into org/model format
        if "/" in repo_id:
            org, model = repo_id.split("/", 1)
        else:
            org = ""
            model = repo_id

        return self.hf_dir / org / f"{model}@{revision}"

    def load_registry(self) -> Dict[str, Any]:
        """Load registry.json file.

        Returns:
            Registry data dictionary
        """
        if not self.registry_file.exists():
            return {"models": {}}

        with open(self.registry_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_registry(self, registry_data: Dict[str, Any]) -> None:
        """Save registry.json file.

        Args:
            registry_data: Registry data to save
        """
        self.ensure_directories()
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(registry_data, f, indent=2, ensure_ascii=False)

    def load_metadata(self, model_dir: Path) -> Dict[str, Any]:
        """Load metadata.json for a specific model.

        Args:
            model_dir: Model directory

        Returns:
            Metadata dictionary
        """
        metadata_file = model_dir / "metadata.json"
        if not metadata_file.exists():
            return {"model_hash": None, "last_verified": None, "approved_files": []}

        with open(metadata_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_metadata(self, model_dir: Path, metadata: Dict[str, Any]) -> None:
        """Save metadata.json for a specific model.

        Args:
            model_dir: Model directory
            metadata: Metadata to save
        """
        model_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = model_dir / "metadata.json"

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def save_file_content(self, model_dir: Path, filename: str, content: str) -> None:
        """Save file content to model's files directory.

        Args:
            model_dir: Model directory
            filename: Original filename
            content: File content to save
        """
        files_dir = model_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        file_path = files_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def load_file_content(self, model_dir: Path, filename: str) -> Optional[str]:
        """Load file content from model's files directory.

        Args:
            model_dir: Model directory
            filename: Filename to load

        Returns:
            File content or None if file doesn't exist
        """
        file_path = model_dir / "files" / filename
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def save_original_path(self, model_dir: Path, original_path: str) -> None:
        """Save original path information for local models.

        Args:
            model_dir: Model directory
            original_path: Original model path
        """
        model_dir.mkdir(parents=True, exist_ok=True)
        path_file = model_dir / "original_path.txt"

        with open(path_file, "w", encoding="utf-8") as f:
            f.write(original_path)

    def load_original_path(self, model_dir: Path) -> Optional[str]:
        """Load original path information for local models.

        Args:
            model_dir: Model directory

        Returns:
            Original model path or None if not found
        """
        path_file = model_dir / "original_path.txt"
        if not path_file.exists():
            return None

        with open(path_file, "r", encoding="utf-8") as f:
            return f.read().strip()

    def get_model_key(self, model_type: str, model_id: str) -> str:
        """Generate model key for registry.

        Args:
            model_type: "hf" or "local"
            model_id: Model identifier

        Returns:
            Model key for registry
        """
        return f"{model_type}/{model_id}"

    def register_model(self, model_type: str, model_id: str, **kwargs) -> None:
        """Register a model in the registry.

        Args:
            model_type: "hf" or "local"
            model_id: Model identifier
            **kwargs: Additional model information
        """
        registry = self.load_registry()
        model_key = self.get_model_key(model_type, model_id)

        model_info = {
            "type": model_type,
            "last_verified": self.get_current_timestamp(),
            "status": "verified",
            **kwargs,
        }

        registry["models"][model_key] = model_info
        self.save_registry(registry)
