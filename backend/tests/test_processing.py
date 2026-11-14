from astropy.time import Time

from astronomy_backend.processing import normalize_observation, normalize_results


def test_normalize_observation_preserves_metadata_and_parses_fields() -> None:
    row = {
        "obs_id": "observation-1",
        "s_ra": 12.5,
        "s_dec": -4.25,
        "instrument_name": "Example Camera",
        "obs_collection": "example_collection",
        "t_min": 60000.0,
        "t_exptime": 30,
        "access_url": "https://example.test/image.fits",
        "access_format": "image/fits",
        "source_flag": "preserved",
    }

    observation = normalize_observation(row)

    assert observation.observation_id == "observation-1"
    assert observation.coordinates is not None
    assert observation.coordinates.ra.deg == 12.5
    assert observation.coordinates.dec.deg == -4.25
    assert observation.observation_time is not None
    assert observation.observation_time.mjd == Time(60000, format="mjd").mjd
    assert observation.exposure_seconds == 30
    assert observation.access_url.endswith("image.fits")
    assert observation.original_metadata["source_flag"] == "preserved"


def test_normalize_observation_handles_missing_and_invalid_optional_values() -> None:
    observation = normalize_observation(
        {
            "obs_id": "",
            "s_ra": 12.5,
            "s_dec": 95,
            "t_min": "not-a-time",
            "t_exptime": "not-a-number",
        }
    )

    assert observation.observation_id is None
    assert observation.coordinates is None
    assert observation.observation_time is None
    assert observation.exposure_seconds is None


def test_normalize_observation_rejects_non_finite_coordinates() -> None:
    observation = normalize_observation(
        {"s_ra": float("nan"), "s_dec": float("inf")}
    )

    assert observation.coordinates is None


def test_normalize_results_returns_one_observation_per_row() -> None:
    observations = normalize_results(
        [{"obs_id": "one"}, {"obs_id": "two"}]
    )

    assert [item.observation_id for item in observations] == ["one", "two"]


def test_normalize_results_skips_malformed_row_and_keeps_valid_rows() -> None:
    observations = normalize_results([{"obs_id": "valid"}, None])  # type: ignore[list-item]

    assert [item.observation_id for item in observations] == ["valid"]
