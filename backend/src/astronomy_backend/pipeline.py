"""End-to-end orchestration for astronomical observation retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .exceptions import (
    CacheError,
    DownloadError,
    FITSProcessingError,
    IRSAError,
    InvalidQueryError,
)
from .fits_handler import FitsMetadata, read_fits_metadata
from .irsa import IRSAClient
from .models import ImageProduct, Observation, ProcessingResult, Query
from .products import ProductDownloader, discover_products
from .cache import FileCache, query_cache_key
from .processing import normalize_observation


@dataclass(frozen=True)
class PipelineResult:
    """Structured result of one pipeline execution."""

    status: str
    query: Query
    observations: tuple[Observation, ...] = ()
    products: tuple[ImageProduct, ...] = ()
    processing_results: tuple[ProcessingResult, ...] = ()
    errors: tuple[str, ...] = ()


class AstronomyPipeline:
    """Coordinate archive querying and optional local product processing."""

    def __init__(
        self,
        irsa_client: IRSAClient,
        product_downloader: ProductDownloader | None = None,
        cache: FileCache | None = None,
    ) -> None:
        self.irsa_client = irsa_client
        self.product_downloader = product_downloader
        self.cache = cache

    def run(
        self,
        query: Query,
        *,
        max_records: int | None = 100,
        download_products: bool = False,
        process_fits: bool = False,
    ) -> PipelineResult:
        """Run the query and optional download/FITS stages."""

        try:
            observations = self._cached_search(query, max_records)
        except InvalidQueryError as exc:
            return PipelineResult("invalid_query", query, errors=(str(exc),))
        except IRSAError as exc:
            return PipelineResult("query_failed", query, errors=(str(exc),))

        products = tuple(discover_products(observations))
        if not observations:
            return PipelineResult("empty", query, products=products)

        errors: list[str] = []
        processing_results: list[ProcessingResult] = []
        if download_products or process_fits:
            if self.product_downloader is None:
                errors.append("Product downloading was requested but no downloader is configured.")
            else:
                processing_results, product_errors = self._process_products(
                    observations,
                    products,
                    download_products=download_products,
                    process_fits=process_fits,
                )
                errors.extend(product_errors)

        status = "partial" if errors else "success"
        return PipelineResult(
            status=status,
            query=query,
            observations=observations,
            products=products,
            processing_results=tuple(processing_results),
            errors=tuple(errors),
        )

    def _cached_search(
        self, query: Query, max_records: int | None
    ) -> tuple[Observation, ...]:
        if self.cache is None or not self.cache.enabled:
            return tuple(self.irsa_client.search(query, max_records=max_records))
        key = query_cache_key(query) + f"-{max_records}"
        try:
            cached = self.cache.get_json(key)
            if cached is not None:
                return tuple(normalize_observation(row) for row in cached)
            observations = tuple(self.irsa_client.search(query, max_records=max_records))
            self.cache.put_json(
                key,
                [
                    {
                        "obs_id": observation.observation_id,
                        "s_ra": observation.coordinates.ra.deg
                        if observation.coordinates
                        else None,
                        "s_dec": observation.coordinates.dec.deg
                        if observation.coordinates
                        else None,
                        "instrument_name": observation.instrument,
                        "obs_collection": observation.collection,
                        "t_min": observation.observation_time.mjd
                        if observation.observation_time
                        else None,
                        "t_exptime": observation.exposure_seconds,
                        "access_url": observation.access_url,
                        "access_format": observation.image_format,
                        **observation.original_metadata,
                    }
                    for observation in observations
                ],
            )
            return observations
        except CacheError:
            return tuple(self.irsa_client.search(query, max_records=max_records))

    def _process_products(
        self,
        observations: tuple[Observation, ...],
        products: tuple[ImageProduct, ...],
        *,
        download_products: bool,
        process_fits: bool,
    ) -> tuple[list[ProcessingResult], list[str]]:
        products_by_url = {product.url: product for product in products}
        results: list[ProcessingResult] = []
        errors: list[str] = []
        for observation in observations:
            if observation.access_url not in products_by_url:
                continue
            product = products_by_url[observation.access_url]
            local_path: Path | None = None
            try:
                if download_products or process_fits:
                    local_path = self.product_downloader.download(product)
                fits_metadata: FitsMetadata | None = None
                status = "downloaded" if local_path else "discovered"
                if process_fits and local_path is not None:
                    fits_metadata = read_fits_metadata(local_path)
                    status = "processed"
                results.append(
                    ProcessingResult(
                        observation=observation,
                        status=status,
                        fits_metadata=fits_metadata,
                    )
                )
            except (DownloadError, FITSProcessingError) as exc:
                message = f"{observation.observation_id or 'observation'}: {exc}"
                errors.append(message)
                results.append(
                    ProcessingResult(
                        observation=observation,
                        status="failed",
                        error=str(exc),
                    )
                )
        return results, errors
