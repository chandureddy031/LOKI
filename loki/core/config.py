"""Configuration management."""

import json
from pathlib import Path


class ConfigManager:
    """Manages ~/.loki/config.json."""

    def __init__(self):
        self.config_dir = Path.home() / ".loki"
        self.config_path = self.config_dir / "config.json"
        self.config = self._load()

    def _load(self) -> dict:
        """Load config from disk."""
        if not self.config_path.exists():
            return self._default_config()

        try:
            with open(self.config_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return self._default_config()

    def _save(self) -> None:
        """Save config to disk."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def _default_config(self) -> dict:
        """Return default configuration."""
        return {
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "scan_extensions": [".py", ".js", ".ts", ".go", ".rs"],
            "ignore_patterns": [
                "node_modules",
                "__pycache__",
                ".git",
                "venv",
                ".venv",
                "env",
                ".env",
                "*.pyc",
                ".mypy_cache",
                ".pytest_cache",
            ],
        }

    def get_provider(self) -> str:
        """Get current provider."""
        return self.config.get("provider", "groq")

    def set_provider(self, provider: str) -> None:
        """Set current provider."""
        self.config["provider"] = provider
        self._save()

    def get_model(self) -> str:
        """Get current model."""
        return self.config.get("model", "llama-3.3-70b-versatile")

    def set_model(self, model: str) -> None:
        """Set current model."""
        self.config["model"] = model
        self._save()

    def get_extensions(self) -> list[str]:
        """Get scan extensions."""
        return self.config.get("scan_extensions", [".py"])

    def get_ignore_patterns(self) -> list[str]:
        """Get ignore patterns."""
        return self.config.get("ignore_patterns", [])
