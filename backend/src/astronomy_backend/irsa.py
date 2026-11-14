"""Reusable PyVO client for the IRSA SIA2 service."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pyvo
import requests
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.units import Quantity
from pyvo.dal.exceptions import DALFormatError, DALQueryError, DALServiceError

from .exceptions import (
    IRSAConnectionError,
    IRSAResponseError,
    InvalidQueryError,
)
from .models import Observation, Query
from .processing import normalize_results
from .pyvo_client import create_sia2_service, execute_sia2_search

DEFAULT_IRSA_SIA2_URL = "https://irsa.ipac.caltech.edu/SIA"


def create_query(
    ra: float | Quantity,
    dec: float | Quantity,
    radius: float | Quantity,
    collection: str | None = None,
    frame: str = "icrs",
    time_start: object | None = None,
    time_end: object | None = None,
    extra_parameters: tuple[tuple[str, str], ...] = (),
) -> Query:
    """Validate angular inputs and create an ICRS-normalized query.

    Numeric values are interpreted as degrees. Quantity values may use any
    angular unit supported by Astropy. Equatorial frames supported by
    ``SkyCoord`` can be supplied and are transformed to ICRS.
    """

    try:
        ra_angle = _as_angle(ra, "RA")
        dec_angle = _as_angle(dec, "Dec")
        radius_angle = _as_angle(radius, "Search radius")
        ra_degrees = ra_angle.to_value(u.deg)
        dec_degrees = dec_angle.to_value(u.deg)
        radius_degrees = radius_angle.to_value(u.deg)
    except (TypeError, ValueError, u.UnitConversionError) as exc:
        raise InvalidQueryError(
            "RA, Dec, and radius must be finite angular values."
        ) from exc

    if not all(math.isfinite(value) for value in (ra_degrees, dec_degrees, radius_degrees)):
        raise InvalidQueryError("RA, Dec, and radius must be finite.")
    if not 0 <= ra_degrees < 360:
        raise InvalidQueryError("RA must be in the range [0, 360) degrees.")
    if not -90 <= dec_degrees <= 90:
        raise InvalidQueryError("Dec must be in the range [-90, 90] degrees.")
    if not 0 < radius_degrees <= 90:
        raise InvalidQueryError("Search radius must be greater than 0 and at most 90 degrees.")
    if collection is not None and not collection.strip():
        raise InvalidQueryError("Collection must not be empty.")

    try:
        coordinates = SkyCoord(
            ra=ra_angle,
            dec=dec_angle,
            frame=frame,
        ).transform_to("icrs")
    except (TypeError, ValueError) as exc:
        raise InvalidQueryError("Unable to construct ICRS coordinates.") from exc

    parsed_start, parsed_end = _parse_time_range(time_start, time_end)

    return Query(
        coordinates=coordinates,
        radius=radius_angle,
        collection=collection,
        submitted_at=datetime.now(timezone.utc),
        time_start=parsed_start,
        time_end=parsed_end,
        extra_parameters=tuple(sorted(extra_parameters)),
    )


def _parse_time_range(start: object | None, end: object | None) -> tuple[object | None, object | None]:
    if start is None and end is None:
        return None, None
    if start is None or end is None:
        raise InvalidQueryError("Both time_start and time_end are required.")
    from astropy.time import Time

    try:
        parsed_start = start if isinstance(start, Time) else Time(start, scale="utc")
        parsed_end = end if isinstance(end, Time) else Time(end, scale="utc")
        if not (math.isfinite(parsed_start.jd) and math.isfinite(parsed_end.jd)):
            raise ValueError("Time values must be finite.")
        if parsed_start > parsed_end:
            raise ValueError("time_start must not exceed time_end.")
        return parsed_start, parsed_end
    except (TypeError, ValueError) as exc:
        raise InvalidQueryError(f"Invalid observation time range: {exc}") from exc


def _as_angle(value: float | Quantity, name: str) -> Quantity:
    if isinstance(value, Quantity):
        if not value.isscalar or not value.unit.is_equivalent(u.deg):
            raise InvalidQueryError(f"{name} must use an angular unit.")
        return value.to(u.deg)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value * u.deg
    raise InvalidQueryError(f"{name} must be numeric or an Astropy quantity.")


class IRSAClient:
    """Query IRSA SIA2 and return normalized observation metadata."""

    def __init__(
        self,
        service_url: str = DEFAULT_IRSA_SIA2_URL,
        timeout_seconds: float = 30,
    ) -> None:
        if not isinstance(service_url, str) or not service_url.strip():
            raise ValueError("IRSA service URL must not be empty.")
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("IRSA timeout must be greater than zero.")
        self.service_url = service_url
        self.timeout_seconds = timeout_seconds
        self._service: pyvo.dal.sia2.SIA2Service | None = None

    @property
    def service(self) -> pyvo.dal.sia2.SIA2Service:
        """Create the PyVO service lazily so client construction stays local."""

        if self._service is None:
            try:
                self._service = create_sia2_service(
                    self.service_url,
                    self.timeout_seconds,
                )
            except DALServiceError as exc:
                raise IRSAConnectionError(
                    f"Unable to initialize the IRSA SIA2 service: {exc}"
                ) from exc
        return self._service

    def search(self, query: Query, max_records: int | None = 100) -> list[Observation]:
        """Execute a SIA2 query and normalize its VOTable records."""

        self._validate_query(query)
        if max_records is not None and (
            not isinstance(max_records, int) or max_records < 0
        ):
            raise InvalidQueryError("max_records must be a non-negative integer or None.")

        try:
            results = execute_sia2_search(self.service, query, max_records)
            rows = (
                {name: row[name] for name in results.fieldnames}
                for row in results
            )
            return normalize_results(rows)
        except requests.exceptions.RequestException as exc:
            raise IRSAConnectionError("The IRSA SIA2 request failed to connect.") from exc
        except DALServiceError as exc:
            cause = exc.cause
            if isinstance(cause, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
                raise IRSAConnectionError(
                    "The IRSA SIA2 request failed to connect."
                ) from exc
            raise IRSAResponseError(f"IRSA SIA2 service error: {exc}") from exc
        except (
            DALFormatError,
            DALQueryError,
            ValueError,
            TypeError,
            AttributeError,
            KeyError,
        ) as exc:
            raise IRSAResponseError(
                f"Unable to parse the IRSA SIA2 response: {exc}"
            ) from exc

    @staticmethod
    def _validate_query(query: Query) -> None:
        if not isinstance(query, Query):
            raise InvalidQueryError("search requires an astronomy Query instance.")
        if not isinstance(query.coordinates, SkyCoord):
            raise InvalidQueryError("Query coordinates must be an Astropy SkyCoord.")
        if query.coordinates.frame.name != "icrs":
            raise InvalidQueryError("Query coordinates must use the ICRS frame.")
        if not isinstance(query.radius, Quantity):
            raise InvalidQueryError("Query radius must be an Astropy quantity.")
        if not query.radius.unit.is_equivalent(u.deg):
            raise InvalidQueryError("Query radius must be angular.")
        if not 0 < query.radius_degrees <= 90:
            raise InvalidQueryError("Search radius must be greater than 0 and at most 90 degrees.")
