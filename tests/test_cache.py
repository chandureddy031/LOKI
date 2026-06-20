"""Tests for cache."""

import tempfile
from pathlib import Path

from loki.core.cache import CacheManager
from loki.core.types import ScanResult


def test_cache_save_and_load():
    """Test cache save and load."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(tmpdir)

        result = ScanResult(
            project_hash="test123",
            created_at=0,
            files=[],
            structure={"directories": [], "entry_points": []},
        )

        cache.save_scan(result)
        loaded = cache.load_scan()

        assert loaded is not None
        assert loaded.project_hash == "test123"


def test_cache_exists():
    """Test cache exists check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(tmpdir)

        assert not cache.exists()

        result = ScanResult(
            project_hash="test123",
            created_at=0,
            files=[],
            structure={"directories": [], "entry_points": []},
        )
        cache.save_scan(result)

        assert cache.exists()
