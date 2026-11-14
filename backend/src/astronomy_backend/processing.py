"""Normalization helpers for VOTable and PyVO result rows."""

from __future__ import annotations

import logging
import math
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time

from .models import Observation

LOGGER = logging.getLogger(__name__)


def _is_missing(value: object) -> bool:
    """Return whether a table value is missing."""

    if value is None or np.ma.is_masked(value):
        return True
    return isinstance(value, str) and not value.strip()


def _first_value(row: Mapping[str, object], *names: str) -> object | None:
    """Return the first present, non-missing value from a row."""

    for name in names:
        if name in row and not _is_missing(row[name]):
            return row[name]
    return None


def _as_text(value: object | None) -> str | None:
    if _is_missing(value):
        return None
    return str(value)


def _as_float(value: object | None) -> float | None:
    if _is_missing(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_time(value: object | None) -> Time | None:
    if _is_missing(value):
        return None
    try:
        if isinstance(value, (int, float, np.number)):
            return Time(value, format="mjd", scale="utc")
        return Time(str(value), scale="utc")
    except (TypeError, ValueError, u.UnitConversionError):
        LOGGER.warning("Unable to parse observation timestamp %r", value)
        return None


def _parse_coordinates(
    ra_value: object | None, dec_value: object | None
) -> SkyCoord | None:
    ra = _as_float(ra_value)
    dec = _as_float(dec_value)
    if ra is None or dec is None:
        return None
    if not math.isfinite(ra) or not math.isfinite(dec):
        LOGGER.warning("Observation coordinates must be finite: RA=%r Dec=%r", ra, dec)
        return None
    try:
        return SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
    except ValueError:
        LOGGER.warning("Unable to parse observation coordinates RA=%r Dec=%r", ra, dec)
        return None


def _to_python_value(value: object) -> Any:
    """Convert common Astropy table scalars to values suitable for storage."""

    if _is_missing(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.ma.MaskedArray):
        return value.tolist()
    return value


def normalize_observation(row: Mapping[str, object]) -> Observation:
    """Convert one VOTable/ObsCore row into an :class:`Observation`.

    Unknown columns are retained in ``original_metadata`` so downstream
    consumers can access source-specific information without losing data.
    """

    original_metadata = {
        str(name): _to_python_value(value) for name, value in row.items()
    }
    return Observation(
        observation_id=_as_text(_first_value(row, "obs_id", "observation_id")),
        coordinates=_parse_coordinates(
            _first_value(row, "s_ra", "ra"),
            _first_value(row, "s_dec", "dec"),
        ),
        instrument=_as_text(_first_value(row, "instrument_name", "instrument")),
        collection=_as_text(_first_value(row, "obs_collection", "collection")),
        observation_time=_parse_time(
            _first_value(row, "t_min", "date_obs", "DATE-OBS")
        ),
        exposure_seconds=_as_float(
            _first_value(row, "t_exptime", "exptime", "EXPTIME")
        ),
        access_url=_as_text(_first_value(row, "access_url", "access_uri")),
        image_format=_as_text(_first_value(row, "access_format", "format")),
        original_metadata=original_metadata,
    )


def normalize_results(rows: Iterable[Mapping[str, object]]) -> list[Observation]:
    """Normalize every row in an already retrieved VOTable result."""

    observations: list[Observation] = []
    for index, row in enumerate(rows):
        try:
            observations.append(normalize_observation(row))
        except (AttributeError, TypeError, ValueError) as exc:
            LOGGER.error("Skipping malformed observation row %d: %s", index, exc)
    return observations
