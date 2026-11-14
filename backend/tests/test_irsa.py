from unittest.mock import Mock, patch

import pytest
import requests
import astropy.units as u

from astronomy_backend.exceptions import (
    IRSAConnectionError,
    IRSAResponseError,
    InvalidQueryError,
)
from astronomy_backend.irsa import IRSAClient, create_query
from pyvo.dal.exceptions import DALServiceError


def test_create_query_validates_coordinates_and_radius() -> None:
    query = create_query(
        12.5 * u.deg,
        -4.25 * u.deg,
        6 * u.arcmin,
        collection="example",
    )

    assert query.coordinates.ra.deg == 12.5
    assert query.coordinates.dec.deg == -4.25
    assert query.radius_degrees == pytest.approx(0.1)
    assert query.collection == "example"


@pytest.mark.parametrize(
    ("ra", "dec", "radius"),
    [(-1, 0, 1), (360, 0, 1), (0, -91, 1), (0, 91, 1), (0, 0, 0)],
)
def test_create_query_rejects_invalid_values(ra: float, dec: float, radius: float) -> None:
    with pytest.raises(InvalidQueryError):
        create_query(ra, dec, radius)


def test_search_normalizes_mocked_result() -> None:
    result = Mock()
    result.fieldnames = ["obs_id", "s_ra", "s_dec"]
    result.__iter__ = lambda self: iter(
        [{"obs_id": "one", "s_ra": 1.0, "s_dec": 2.0}]
    )
    service = Mock()
    service.search.return_value = result
    client = IRSAClient()
    client._service = service

    observations = client.search(create_query(1, 2, 0.1), max_records=1)

    assert observations[0].observation_id == "one"
    service.search.assert_called_once()


def test_search_maps_connection_failure() -> None:
    service = Mock()
    service.search.side_effect = requests.exceptions.Timeout()
    client = IRSAClient()
    client._service = service

    with pytest.raises(IRSAConnectionError):
        client.search(create_query(1, 2, 0.1))


def test_search_maps_malformed_response() -> None:
    service = Mock()
    service.search.side_effect = ValueError("malformed VOTable")
    client = IRSAClient()
    client._service = service

    with pytest.raises(IRSAResponseError):
        client.search(create_query(1, 2, 0.1))


def test_search_maps_service_error() -> None:
    service = Mock()
    service.search.side_effect = DALServiceError("HTTP 500")
    client = IRSAClient()
    client._service = service

    with pytest.raises(IRSAResponseError):
        client.search(create_query(1, 2, 0.1))


def test_create_query_transforms_supported_equatorial_frame_to_icrs() -> None:
    query = create_query(12.5, -4.25, 0.1, frame="fk5")

    assert query.coordinates.frame.name == "icrs"


def test_create_query_rejects_non_angular_quantity() -> None:
    with pytest.raises(InvalidQueryError):
        create_query(12.5 * u.m, -4.25 * u.deg, 0.1 * u.deg)


def test_create_query_rejects_non_finite_values() -> None:
    with pytest.raises(InvalidQueryError):
        create_query(float("nan"), -4.25, 0.1)


def test_create_query_rejects_array_valued_angles() -> None:
    with pytest.raises(InvalidQueryError):
        create_query([1, 2], -4.25, 0.1)


def test_client_rejects_non_finite_timeout() -> None:
    with pytest.raises(ValueError):
        IRSAClient(timeout_seconds=float("inf"))
