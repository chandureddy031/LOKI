"""Secure API key storage using OS keychain."""

import hashlib
import re
from pathlib import Path

import keyring


class SecurityError(Exception):
    """Security-related error."""
    pass


class SecretManager:
    """Manages API keys in OS keychain."""

    SERVICE_NAME = "loki-cli"

    PATTERNS = {
        "groq": r"^gsk_[a-zA-Z0-9]{48,}$",
        "openai": r"^sk-[a-zA-Z0-9]{48,}$",
        "anthropic": r"^sk-ant-[a-zA-Z0-9]{48,}$",
        "openrouter": r"^sk-or-[a-zA-Z0-9]{48,}$",
    }

    def __init__(self):
        self.config_path = Path.home() / ".loki" / "config.json"

    def store_key(self, provider: str, api_key: str) -> None:
        """Store API key in OS keychain."""
        if not self._validate_key_format(provider, api_key):
            raise SecurityError(f"Invalid {provider} API key format")

        keyring.set_password(self.SERVICE_NAME, provider, api_key)

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        self._update_config_hash(provider, key_hash)

    def retrieve_key(self, provider: str) -> str | None:
        """Retrieve API key from OS keychain."""
        key = keyring.get_password(self.SERVICE_NAME, provider)
        if key is None:
            return None

        key_hash = hashlib.sha256(key.encode()).hexdigest()
        if not self._verify_config_hash(provider, key_hash):
            self.delete_key(provider)
            raise SecurityError("API key integrity check failed")

        return key

    def delete_key(self, provider: str) -> None:
        """Delete API key from keychain."""
        try:
            keyring.delete_password(self.SERVICE_NAME, provider)
        except keyring.errors.PasswordDeleteError:
            pass
        self._remove_config_hash(provider)

    def _validate_key_format(self, provider: str, key: str) -> bool:
        """Validate key format."""
        pattern = self.PATTERNS.get(provider)
        if not pattern:
            return False
        return bool(re.match(pattern, key))

    def _update_config_hash(self, provider: str, key_hash: str) -> None:
        """Update hash in config file."""
        import json

        config = {}
        if self.config_path.exists():
            with open(self.config_path) as f:
                config = json.load(f)

        config[f"{provider}_key_hash"] = key_hash

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _verify_config_hash(self, provider: str, key_hash: str) -> bool:
        """Verify hash matches config."""
        import json

        if not self.config_path.exists():
            return True

        with open(self.config_path) as f:
            config = json.load(f)

        stored_hash = config.get(f"{provider}_key_hash")
        if stored_hash is None:
            return True

        return stored_hash == key_hash

    def _remove_config_hash(self, provider: str) -> None:
        """Remove hash from config."""
        import json

        if not self.config_path.exists():
            return

        with open(self.config_path) as f:
            config = json.load(f)

        config.pop(f"{provider}_key_hash", None)

        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)
