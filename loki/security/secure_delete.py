"""Secure file deletion."""

import os
from pathlib import Path


class SecureDeleter:
    """Securely delete files and directories."""

    def secure_delete(self, file_path: Path, passes: int = 3) -> None:
        """Overwrite file before deletion."""
        if not file_path.exists():
            return

        file_size = file_path.stat().st_size

        for _ in range(passes):
            with open(file_path, "wb") as f:
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())

        file_path.unlink()

    def secure_delete_dir(self, dir_path: Path) -> None:
        """Securely delete entire directory."""
        if not dir_path.exists():
            return

        files = sorted(dir_path.rglob("*"), reverse=True)
        for item in files:
            if item.is_file():
                self.secure_delete(item)
            elif item.is_dir():
                try:
                    item.rmdir()
                except OSError:
                    pass

        if dir_path.exists():
            dir_path.rmdir()
