"""PyVO-specific service and SIA2 query helpers."""

from __future__ import annotations

import math
from typing import Any

import pyvo
import requests
from astropy.coordinates import SkyCoord
from pyvo.dal.sia2 import SIA2Results

from .models import Query


class TimeoutSession(requests.Session):
    """Requests session that applies a timeout to every request."""

    def __init__(self, timeout_seconds: float) -> None:
        super().__init__()
        self._timeout_seconds = timeout_seconds

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self._timeout_seconds)
        return super().request(method, url, **kwargs)


def create_sia2_service(
    service_url: str,
    timeout_seconds: float,
) -> pyvo.dal.sia2.SIA2Service:
    """Create a PyVO SIA2 service with a bounded HTTP session."""

    if not isinstance(service_url, str) or not service_url.strip():
        raise ValueError("SIA2 service URL must not be empty.")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("SIA2 timeout must be greater than zero.")
    return pyvo.dal.SIA2Service(
        service_url,
        session=TimeoutSession(timeout_seconds),
    )


def execute_sia2_search(
    service: pyvo.dal.sia2.SIA2Service,
    query: Query,
    max_records: int | None,
) -> SIA2Results:
    """Submit a normalized query through PyVO's SIA2 abstraction."""

    coordinates = query.coordinates.icrs
    parameters = dict(
        pos=(
            float(coordinates.ra.deg),
            float(coordinates.dec.deg),
            query.radius_degrees,
        ),
        collection=query.collection,
        maxrec=max_records,
        res_format="VOTABLE",
    )
    if query.time_interval is not None:
        parameters["time"] = query.time_interval
    return service.search(
        **parameters,
    )
