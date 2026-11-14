from unittest.mock import Mock

from astronomy_backend.exceptions import IRSAConnectionError
from astronomy_backend.exceptions import DownloadError
from astronomy_backend.cache import FileCache
from astronomy_backend.irsa import create_query
from astronomy_backend.models import Observation
from astronomy_backend.pipeline import AstronomyPipeline


def _observation(url: str | None = None) -> Observation:
    return Observation(
        observation_id="obs-1",
        coordinates=None,
        instrument=None,
        collection=None,
        observation_time=None,
        exposure_seconds=None,
        access_url=url,
        image_format="image/fits" if url else None,
        original_metadata={},
    )


def test_pipeline_reports_empty_query() -> None:
    client = Mock()
    client.search.return_value = []
    query = create_query(1, 2, 0.1)

    result = AstronomyPipeline(client).run(query)

    assert result.status == "empty"
    assert result.observations == ()


def test_pipeline_returns_observations_and_products() -> None:
    client = Mock()
    client.search.return_value = [_observation("https://example.test/a.fits")]
    query = create_query(1, 2, 0.1)

    result = AstronomyPipeline(client).run(query)

    assert result.status == "success"
    assert len(result.observations) == 1
    assert len(result.products) == 1


def test_pipeline_reports_missing_downloader_as_partial() -> None:
    client = Mock()
    client.search.return_value = [_observation("https://example.test/a.fits")]
    query = create_query(1, 2, 0.1)

    result = AstronomyPipeline(client).run(query, download_products=True)

    assert result.status == "partial"
    assert "no downloader" in result.errors[0].lower()


def test_pipeline_reports_query_failure_without_fabricating_observations() -> None:
    client = Mock()
    client.search.side_effect = IRSAConnectionError("service unavailable")
    query = create_query(1, 2, 0.1)

    result = AstronomyPipeline(client).run(query)

    assert result.status == "query_failed"
    assert result.observations == ()
    assert result.errors == ("service unavailable",)


def test_pipeline_preserves_metadata_when_product_download_fails() -> None:
    client = Mock()
    client.search.return_value = [_observation("https://example.test/a.fits")]
    downloader = Mock()
    downloader.download.side_effect = DownloadError("download failed")
    query = create_query(1, 2, 0.1)

    result = AstronomyPipeline(client, downloader).run(
        query,
        download_products=True,
    )

    assert result.status == "partial"
    assert len(result.observations) == 1
    assert result.processing_results[0].status == "failed"


def test_pipeline_uses_optional_cache_on_second_query(tmp_path) -> None:
    client = Mock()
    client.search.return_value = [_observation()]
    pipeline = AstronomyPipeline(client, cache=FileCache(tmp_path))
    query = create_query(1, 2, 0.1)

    pipeline.run(query)
    pipeline.run(query)

    client.search.assert_called_once()
