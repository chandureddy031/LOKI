"""Tests for commands."""

import tempfile
from pathlib import Path

from loki.commands.init_cmd import execute_init
from loki.core.cache import CacheManager


def test_init_creates_cache():
    """Test init command creates cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "test.py").write_text("print('hello')")

        import os
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        try:
            execute_init(tmpdir)

            cache = CacheManager(tmpdir)
            assert cache.exists()
        finally:
            os.chdir(original_dir)
