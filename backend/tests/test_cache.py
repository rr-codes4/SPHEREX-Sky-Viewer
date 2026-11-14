import json
import os
import time
from pathlib import Path

import astropy.units as u

from astronomy_backend.cache import FileCache, query_cache_key
from astronomy_backend.irsa import create_query


def test_cache_hit_and_miss(tmp_path: Path) -> None:
    cache = FileCache(tmp_path)
    assert cache.get_json("missing") is None
    cache.put_json("entry", {"value": 1})
    assert cache.get_json("entry") == {"value": 1}
    assert cache.stats.hits == 1
    assert cache.stats.misses == 1


def test_cache_expiration_invalidation_and_clear(tmp_path: Path) -> None:
    cache = FileCache(tmp_path, ttl_seconds=1)
    cache.put_bytes("entry", b"data")
    old = time.time() - 10
    os.utime(tmp_path / "entry.bin", (old, old))
    assert cache.get_bytes("entry") is None
    cache.put_json("one", {"a": 1})
    cache.invalidate("one")
    assert cache.get_json("one") is None
    cache.put_json("two", {"b": 2})
    cache.clear()
    assert list(tmp_path.iterdir()) == []


def test_cache_detects_corruption_and_disabled_mode(tmp_path: Path) -> None:
    cache = FileCache(tmp_path)
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    try:
        cache.get_json("bad")
    except Exception as exc:
        assert "Corrupted" in str(exc)
    disabled = FileCache(tmp_path / "disabled", enabled=False)
    disabled.put_json("entry", {"value": 1})
    assert disabled.get_json("entry") is None
    (tmp_path / "empty.bin").write_bytes(b"")
    assert cache.get_bytes("empty") is None


def test_query_cache_keys_include_query_parameters() -> None:
    first = create_query(1, 2, 0.1, collection="one")
    second = create_query(1, 2, 0.1, collection="two")
    assert query_cache_key(first) != query_cache_key(second)
