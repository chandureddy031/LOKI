"""Tests for scanner."""

import tempfile
from pathlib import Path

from loki.core.scanner import FileScanner


def test_scanner_finds_python_files():
    """Test scanner finds Python files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "test.py").write_text("print('hello')")
        (Path(tmpdir) / "readme.txt").write_text("not python")

        scanner = FileScanner(tmpdir, [])
        result = scanner.scan()

        assert len(result.files) == 1
        assert result.files[0].path == "test.py"


def test_scanner_respects_ignore_patterns():
    """Test scanner respects ignore patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "test.py").write_text("print('hello')")
        (Path(tmpdir) / "__pycache__").mkdir()
        (Path(tmpdir) / "__pycache__" / "cached.py").write_text("cached")

        scanner = FileScanner(tmpdir, ["__pycache__"])
        result = scanner.scan()

        assert len(result.files) == 1
