"""Cache management for project data."""

import hashlib
import time
from pathlib import Path

from .types import Error, ScanResult
from ..security.cache_security import SecureCache


class CacheManager:
    """Manages local cache in ~/.loki/{project_hash}/."""

    SCAN_TTL = 300

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir).resolve()
        self.project_hash = self._compute_hash()
        self.cache_dir = Path.home() / ".loki" / self.project_hash
        self.secure_cache = SecureCache(self.cache_dir)

    def _compute_hash(self) -> str:
        """Compute SHA256 hash of project path."""
        return hashlib.sha256(str(self.project_dir).encode()).hexdigest()[:12]

    def save_scan(self, result: ScanResult) -> None:
        """Save scan result."""
        from dataclasses import asdict
        self.secure_cache.save_encrypted("scan.json", asdict(result))

    def load_scan(self) -> ScanResult | None:
        """Load scan result from cache."""
        if not self.secure_cache.file_exists("scan.json"):
            return None

        try:
            data = self.secure_cache.load_encrypted("scan.json")
            return ScanResult(**data)
        except Exception:
            return None

    def save_errors(self, errors: list[Error]) -> None:
        """Save errors."""
        from dataclasses import asdict
        self.secure_cache.save_encrypted("errors.json", {"errors": [asdict(e) for e in errors]})

    def load_errors(self) -> list[Error]:
        """Load errors from cache."""
        if not self.secure_cache.file_exists("errors.json"):
            return []

        try:
            data = self.secure_cache.load_encrypted("errors.json")
            return [Error(**e) for e in data.get("errors", [])]
        except Exception:
            return []

    def is_stale(self) -> bool:
        """Check if cache is older than TTL."""
        scan = self.load_scan()
        if scan is None:
            return True
        return (time.time() - scan.created_at) > self.SCAN_TTL

    def exists(self) -> bool:
        """Check if cache exists."""
        return self.secure_cache.file_exists("scan.json")

    def clear(self) -> None:
        """Delete entire cache directory."""
        from ..security.secure_delete import SecureDeleter
        deleter = SecureDeleter()
        deleter.secure_delete_dir(self.cache_dir)

    def get_cache_dir(self) -> Path:
        """Get cache directory path."""
        return self.cache_dir
