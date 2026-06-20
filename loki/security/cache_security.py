"""Encrypted cache storage."""

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet
import keyring


class CacheError(Exception):
    """Cache-related error."""
    pass


class SecureCache:
    """Manages encrypted cache files."""

    KEY_SERVICE = "loki-cache"
    KEY_NAME = "encryption-key"

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        try:
            key_str = keyring.get_password(self.KEY_SERVICE, self.KEY_NAME)
            if key_str is not None:
                return key_str.encode()
        except Exception:
            pass

        key = Fernet.generate_key()
        try:
            keyring.set_password(self.KEY_SERVICE, self.KEY_NAME, key.decode())
        except Exception:
            pass
        return key

    def save_encrypted(self, filename: str, data: dict) -> None:
        """Save data encrypted to disk."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        json_data = json.dumps(data, default=str).encode()
        encrypted = self.cipher.encrypt(json_data)

        file_path = self.cache_dir / filename
        file_path.write_bytes(encrypted)

        self._set_restrictive_permissions(file_path)

    def load_encrypted(self, filename: str) -> dict:
        """Load and decrypt data from disk."""
        file_path = self.cache_dir / filename
        if not file_path.exists():
            raise CacheError(f"Cache file not found: {filename}")

        encrypted = file_path.read_bytes()
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted)

    def file_exists(self, filename: str) -> bool:
        """Check if cache file exists."""
        return (self.cache_dir / filename).exists()

    def _set_restrictive_permissions(self, file_path: Path) -> None:
        """Set restrictive file permissions."""
        if os.name != "nt":
            os.chmod(file_path, 0o600)
