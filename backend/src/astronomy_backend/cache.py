"""Deterministic, filesystem-backed cache for query and product payloads."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import astropy.units as u

from .exceptions import CacheError
from .models import Query


@dataclass(frozen=True)
class CacheStats:
    """Cache hit/miss counters for one cache instance."""

    hits: int
    misses: int


def query_cache_key(query: Query) -> str:
    """Create a stable key from all query parameters affecting results."""

    payload = {
        "ra_degrees": round(float(query.coordinates.icrs.ra.deg), 12),
        "dec_degrees": round(float(query.coordinates.icrs.dec.deg), 12),
        "radius_degrees": round(query.radius_degrees, 12),
        "radius_unit": str(query.radius.unit),
        "collection": query.collection,
        "time_start": query.time_start.isot if query.time_start else None,
        "time_end": query.time_end.isot if query.time_end else None,
        "extra_parameters": list(query.extra_parameters),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class FileCache:
    """A small atomic JSON/bytes cache with TTL and optional disabling."""

    def __init__(
        self,
        directory: str | Path,
        *,
        ttl_seconds: float = 3600,
        enabled: bool = True,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("Cache TTL must be greater than zero.")
        self.directory = Path(directory).expanduser()
        self.ttl_seconds = ttl_seconds
        self.enabled = enabled
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> CacheStats:
        return CacheStats(self._hits, self._misses)

    def _path(self, key: str, suffix: str) -> Path:
        if not key or "/" in key or "\\" in key:
            raise CacheError("Cache key must be a non-empty path-safe value.")
        return self.directory / f"{key}.{suffix}"

    def get_bytes(self, key: str) -> bytes | None:
        if not self.enabled:
            return None
        path = self._path(key, "bin")
        with self._lock:
            if not self._is_fresh(path):
                self._misses += 1
                return None
            try:
                data = path.read_bytes()
            except OSError as exc:
                self._misses += 1
                raise CacheError(f"Unable to read cache entry {path}: {exc}") from exc
            self._hits += 1
            return data

    def put_bytes(self, key: str, content: bytes) -> None:
        if not self.enabled:
            return
        if not isinstance(content, bytes):
            raise CacheError("Cache content must be bytes.")
        self._atomic_write(self._path(key, "bin"), content)

    def get_json(self, key: str) -> Any | None:
        if not self.enabled:
            return None
        path = self._path(key, "json")
        with self._lock:
            if not self._is_fresh(path):
                self._misses += 1
                return None
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                self._delete(path)
                self._misses += 1
                raise CacheError(f"Corrupted cache entry {path}: {exc}") from exc
            self._hits += 1
            return value

    def put_json(self, key: str, value: Any) -> None:
        if not self.enabled:
            return
        try:
            content = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        except (TypeError, ValueError) as exc:
            raise CacheError(f"Unable to serialize cache entry: {exc}") from exc
        self._atomic_write(self._path(key, "json"), content)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._delete(self._path(key, "bin"))
            self._delete(self._path(key, "json"))

    def clear(self) -> None:
        with self._lock:
            if not self.directory.exists():
                return
            for path in self.directory.iterdir():
                if path.is_file() and path.suffix in {".bin", ".json"}:
                    self._delete(path)

    def _is_fresh(self, path: Path) -> bool:
        if not path.is_file():
            return False
        try:
            if time.time() - path.stat().st_mtime >= self.ttl_seconds:
                self._delete(path)
                return False
            if path.stat().st_size == 0:
                self._delete(path)
                return False
            return True
        except OSError:
            return False

    @staticmethod
    def _delete(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise CacheError(f"Unable to remove cache entry {path}: {exc}") from exc

    def _atomic_write(self, destination: Path, content: bytes) -> None:
        temporary_path: Path | None = None
        with self._lock:
            try:
                self.directory.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(
                    dir=self.directory, prefix=".cache-", suffix=".tmp", delete=False
                ) as output:
                    temporary_path = Path(output.name)
                    output.write(content)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary_path, destination)
                temporary_path = None
            except OSError as exc:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)
                raise CacheError(f"Unable to write cache entry {destination}: {exc}") from exc
