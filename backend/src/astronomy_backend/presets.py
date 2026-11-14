"""Validated astronomical target presets loaded from JSON."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import astropy.units as u
from astropy.time import Time

from .exceptions import PresetValidationError
from .exceptions import InvalidQueryError
from .irsa import create_query
from .models import Query

_COLLECTION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


@dataclass(frozen=True)
class TargetPreset:
    """A named astronomical target and its archive query constraints."""

    target_id: str
    name: str
    ra: float
    dec: float
    coordinate_unit: str
    radius: float
    radius_unit: str
    collection: str
    time_start: str | None = None
    time_end: str | None = None
    description: str | None = None

    def to_query(self) -> Query:
        """Convert this validated preset into the standard backend Query."""

        return create_query(
            self.ra * u.Unit(self.coordinate_unit),
            self.dec * u.Unit(self.coordinate_unit),
            self.radius * u.Unit(self.radius_unit),
            collection=self.collection,
            time_start=self.time_start,
            time_end=self.time_end,
        )


def validate_preset(data: Any) -> TargetPreset:
    """Validate one decoded JSON preset and return a typed model."""

    if not isinstance(data, dict):
        raise PresetValidationError("Target preset must be a JSON object.")
    required = {
        "target_id", "name", "ra", "dec", "coordinate_unit",
        "radius", "radius_unit", "collection",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise PresetValidationError(f"Missing required preset fields: {', '.join(missing)}.")
    try:
        values = {key: data[key] for key in required}
        values.update({
            key: data.get(key)
            for key in ("time_start", "time_end", "description")
        })
        if not all(isinstance(data[key], str) and data[key].strip() for key in ("target_id", "name", "coordinate_unit", "radius_unit", "collection")):
            raise ValueError("Text fields must be non-empty strings.")
        if not all(isinstance(data[key], (int, float)) and not isinstance(data[key], bool) for key in ("ra", "dec", "radius")):
            raise ValueError("RA, Dec, and radius must be numeric.")
        for key in ("time_start", "time_end", "description"):
            if data.get(key) is not None and not isinstance(data[key], str):
                raise ValueError(f"{key} must be a string when provided.")
        coordinate_unit = u.Unit(data["coordinate_unit"])
        radius_unit = u.Unit(data["radius_unit"])
        if not coordinate_unit.is_equivalent(u.deg) or not radius_unit.is_equivalent(u.deg):
            raise ValueError("Coordinate and radius units must be angular.")
        if not _COLLECTION_PATTERN.fullmatch(data["collection"]):
            raise ValueError("Collection identifier has invalid syntax.")
        preset = TargetPreset(**values)
        preset.to_query()
        return preset
    except (TypeError, ValueError, u.UnitConversionError, InvalidQueryError) as exc:
        raise PresetValidationError(str(exc)) from exc


def load_presets(path: str | Path) -> dict[str, TargetPreset]:
    """Load and validate a JSON object or list of target presets."""

    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PresetValidationError(f"Unable to load presets: {exc}") from exc
    entries = data.get("presets") if isinstance(data, dict) and "presets" in data else data
    if not isinstance(entries, list):
        raise PresetValidationError("Preset file must contain a list or a 'presets' list.")
    presets: dict[str, TargetPreset] = {}
    for entry in entries:
        preset = validate_preset(entry)
        if preset.target_id in presets:
            raise PresetValidationError(f"Duplicate target_id: {preset.target_id}")
        presets[preset.target_id] = preset
    return presets
