"""Local filesystem storage for raw responses and processed metadata."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

from .config import BackendSettings
from .exceptions import StorageError


class FileStorage:
    """Store backend artifacts under separate raw and processed directories."""

    def __init__(
        self,
        raw_directory: str | Path | None = None,
        processed_directory: str | Path | None = None,
    ) -> None:
        settings = BackendSettings.from_environment()
        self.raw_directory = Path(raw_directory or settings.raw_data_directory).expanduser()
        self.processed_directory = Path(
            processed_directory or settings.processed_data_directory
        ).expanduser()

    def save_raw_votable(self, content: bytes, filename: str) -> Path:
        """Store raw VOTable bytes without overwriting an existing file."""

        if not isinstance(content, bytes):
            raise StorageError("Raw VOTable content must be bytes.")
        return self._write_new(self.raw_directory, filename, content)

    def save_processed_metadata(
        self,
        metadata: Any,
        filename: str,
    ) -> Path:
        """Serialize normalized metadata as deterministic, readable JSON."""

        try:
            content = json.dumps(
                metadata,
                default=_json_default,
                indent=2,
                sort_keys=True,
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise StorageError(f"Unable to serialize processed metadata: {exc}") from exc
        return self._write_new(self.processed_directory, filename, content)

    @staticmethod
    def _write_new(directory: Path, filename: str, content: bytes) -> Path:
        safe_name = _validate_filename(filename)
        destination = directory / safe_name
        temporary_path: Path | None = None
        try:
            directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=directory,
                prefix=f".{safe_name}.",
                suffix=".tmp",
                delete=False,
            ) as output:
                temporary_path = Path(output.name)
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            os.link(temporary_path, destination)
            temporary_path.unlink()
            temporary_path = None
        except OSError as exc:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise StorageError(f"Unable to store backend artifact {destination}: {exc}") from exc
        return destination


def _validate_filename(filename: str) -> str:
    if not isinstance(filename, str):
        raise StorageError("Storage filename must be a string.")
    path = Path(filename)
    if (
        not filename
        or path.name != filename
        or "\\" in filename
        or filename in {".", ".."}
    ):
        raise StorageError(f"Unsafe storage filename: {filename!r}")
    return filename


def _json_default(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, SkyCoord):
        return {
            "frame": value.frame.name,
            "ra_degrees": value.icrs.ra.deg,
            "dec_degrees": value.icrs.dec.deg,
        }
    if isinstance(value, Time):
        return value.isot
    if isinstance(value, u.Quantity):
        return {"value": value.value.tolist() if hasattr(value.value, "tolist") else value.value,
                "unit": str(value.unit)}
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Unsupported metadata type: {type(value).__name__}")
