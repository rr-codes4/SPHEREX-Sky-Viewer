"""Internal data models for astronomical queries and observations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time


@dataclass(frozen=True)
class Query:
    """A validated spatial archive query."""

    coordinates: SkyCoord
    radius: u.Quantity
    collection: str | None = None
    submitted_at: datetime | None = None
    time_start: Time | None = None
    time_end: Time | None = None
    extra_parameters: tuple[tuple[str, str], ...] = ()

    @property
    def radius_degrees(self) -> float:
        """Return the search radius in the SIA2 standard unit, degrees."""

        return float(self.radius.to_value(u.deg))

    @property
    def time_interval(self) -> tuple[Time, Time] | None:
        """Return the optional inclusive observation-time interval."""

        if self.time_start is None and self.time_end is None:
            return None
        if self.time_start is None or self.time_end is None:
            raise ValueError("Both time_start and time_end are required.")
        return self.time_start, self.time_end


@dataclass(frozen=True)
class Observation:
    """Normalized metadata for one archive observation."""

    observation_id: str | None
    coordinates: SkyCoord | None
    instrument: str | None
    collection: str | None
    observation_time: Time | None
    exposure_seconds: float | None
    access_url: str | None
    image_format: str | None
    original_metadata: dict[str, Any]


@dataclass(frozen=True)
class ImageProduct:
    """A downloadable image product associated with an observation."""

    observation_id: str | None
    url: str
    image_format: str | None


@dataclass(frozen=True)
class ProcessingResult:
    """Outcome of optional processing for one observation."""

    observation: Observation
    status: str
    fits_metadata: object | None = None
    error: str | None = None
