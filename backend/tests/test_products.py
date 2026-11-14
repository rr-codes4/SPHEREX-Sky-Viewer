from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
import requests

from astronomy_backend.exceptions import DownloadError
from astronomy_backend.models import ImageProduct, Observation
from astronomy_backend.products import ProductDownloader, discover_products


def _observation(url: str | None) -> Observation:
    return Observation(
        observation_id="obs/1",
        coordinates=None,
        instrument=None,
        collection=None,
        observation_time=None,
        exposure_seconds=None,
        access_url=url,
        image_format="image/fits",
        original_metadata={},
    )


def test_discover_products_ignores_observations_without_urls() -> None:
    products = discover_products([_observation("https://example.test/a"), _observation(None)])

    assert products == [
        ImageProduct("obs/1", "https://example.test/a", "image/fits")
    ]


def test_downloader_streams_fits_without_overwriting(tmp_path: Path) -> None:
    response = Mock()
    response.iter_content.return_value = [b"SIMPLE  ", b"data"]
    session = MagicMock()
    session.get.return_value.__enter__.return_value = response
    downloader = ProductDownloader(tmp_path, session=session)

    output = downloader.download(
        ImageProduct("obs/1", "https://example.test/a", "image/fits")
    )

    assert output == tmp_path / "obs_1.fits"
    assert output.read_bytes() == b"SIMPLE  data"
    second_output = downloader.download(
        ImageProduct("obs/1", "https://example.test/other", "image/fits")
    )
    assert second_output.name.startswith("obs_1-")


def test_downloader_rejects_unsafe_explicit_filename(tmp_path: Path) -> None:
    downloader = ProductDownloader(tmp_path)

    with pytest.raises(DownloadError):
        downloader.download(
            ImageProduct("obs-1", "https://example.test/a", "image/fits"),
            filename="../outside.fits",
        )


def test_downloader_enforces_optional_size_limit(tmp_path: Path) -> None:
    response = Mock()
    response.headers = {"content-length": "5"}
    response.iter_content.return_value = [b"12345"]
    session = MagicMock()
    session.get.return_value.__enter__.return_value = response
    downloader = ProductDownloader(tmp_path, session=session, max_download_bytes=4)

    with pytest.raises(DownloadError):
        downloader.download(
            ImageProduct("obs-1", "https://example.test/a", "image/fits")
        )
    assert list(tmp_path.iterdir()) == []


def test_downloader_maps_http_failures(tmp_path: Path) -> None:
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("server error")
    session = MagicMock()
    session.get.return_value.__enter__.return_value = response
    downloader = ProductDownloader(tmp_path, session=session)

    with pytest.raises(DownloadError):
        downloader.download(
            ImageProduct("obs-2", "https://example.test/a", "image/fits")
        )
    assert list(tmp_path.iterdir()) == []


def test_downloader_rejects_non_http_urls(tmp_path: Path) -> None:
    downloader = ProductDownloader(tmp_path)

    with pytest.raises(DownloadError):
        downloader.download(ImageProduct("obs-3", "file:///tmp/a.fits", "image/fits"))
