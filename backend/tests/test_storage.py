import json
from pathlib import Path

import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord

from astronomy_backend.exceptions import StorageError
from astronomy_backend.models import Observation, ProcessingResult
from astronomy_backend.storage import FileStorage


def test_storage_separates_raw_and_processed_metadata(tmp_path: Path) -> None:
    storage = FileStorage(tmp_path / "raw", tmp_path / "processed")

    raw_path = storage.save_raw_votable(b"<VOTABLE />", "query.vot")
    processed_path = storage.save_processed_metadata(
        {
            "coordinates": SkyCoord(1 * u.deg, 2 * u.deg),
            "radius": 6 * u.arcmin,
        },
        "observations.json",
    )

    assert raw_path.parent == tmp_path / "raw"
    assert processed_path.parent == tmp_path / "processed"
    payload = json.loads(processed_path.read_text(encoding="utf-8"))
    assert payload["coordinates"]["frame"] == "icrs"
    assert payload["radius"]["unit"] == "arcmin"


def test_storage_rejects_overwrites_and_traversal(tmp_path: Path) -> None:
    storage = FileStorage(tmp_path / "raw", tmp_path / "processed")
    storage.save_raw_votable(b"first", "query.vot")

    with pytest.raises(StorageError):
        storage.save_raw_votable(b"second", "query.vot")
    with pytest.raises(StorageError):
        storage.save_raw_votable(b"unsafe", "../query.vot")


def test_storage_serializes_observation_dataclasses(tmp_path: Path) -> None:
    storage = FileStorage(tmp_path / "raw", tmp_path / "processed")
    observation = Observation(
        observation_id="obs-1",
        coordinates=SkyCoord(1 * u.deg, 2 * u.deg),
        instrument="camera",
        collection="collection",
        observation_time=None,
        exposure_seconds=2.5,
        access_url=None,
        image_format=None,
        original_metadata={"flag": "good"},
    )

    output = storage.save_processed_metadata(
        ProcessingResult(observation=observation, status="processed"),
        "result.json",
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["observation"]["coordinates"]["ra_degrees"] == 1.0
    assert payload["status"] == "processed"
