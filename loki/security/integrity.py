"""Package integrity verification."""

import hashlib
import json
from pathlib import Path


class PackageIntegrity:
    """Verifies package file integrity."""

    MANIFEST_FILE = "loki_manifest.json"

    @classmethod
    def generate_manifest(cls, package_dir: Path) -> dict:
        """Generate file hash manifest."""
        manifest = {}

        for file_path in package_dir.rglob("*"):
            if file_path.is_file() and not file_path.suffix == ".pyc":
                relative_path = str(file_path.relative_to(package_dir))
                file_hash = cls._hash_file(file_path)
                manifest[relative_path] = {
                    "hash": file_hash,
                    "size": file_path.stat().st_size,
                }

        return manifest

    @classmethod
    def verify_manifest(cls, package_dir: Path) -> tuple[bool, list[str]]:
        """Verify package files against manifest."""
        manifest_path = package_dir / cls.MANIFEST_FILE

        if not manifest_path.exists():
            return True, []

        with open(manifest_path) as f:
            stored_manifest = json.load(f)

        current_manifest = cls.generate_manifest(package_dir)

        issues = []
        for file_path, stored_info in stored_manifest.items():
            if file_path not in current_manifest:
                issues.append(f"Missing: {file_path}")
            elif current_manifest[file_path]["hash"] != stored_info["hash"]:
                issues.append(f"Tampered: {file_path}")

        return len(issues) == 0, issues

    @classmethod
    def _hash_file(cls, file_path: Path) -> str:
        """SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
