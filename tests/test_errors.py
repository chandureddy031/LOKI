"""Tests for error detection."""

import tempfile
from pathlib import Path

from loki.core.scanner import FileScanner
from loki.core.errors import ErrorDetector


def test_detect_syntax_errors():
    """Test syntax error detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "bad.py").write_text("def foo(\n")
        (Path(tmpdir) / "good.py").write_text("def foo(): pass")

        scanner = FileScanner(tmpdir, [])
        result = scanner.scan()

        detector = ErrorDetector(result, tmpdir)
        errors = detector.detect_syntax_errors()

        assert len(errors) == 1
        assert errors[0].source == "python_ast"
