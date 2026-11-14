# Architecture

## Modules

- `config.py`: backend paths and environment-based settings.
- `models.py`: immutable query, observation, product, and processing models.
- `pyvo_client.py`: PyVO SIA2 service creation and request submission.
- `irsa.py`: IRSA-facing validation, error translation, and normalization.
- `processing.py`: conversion of ObsCore/VOTable rows into observations.
- `products.py`: product discovery and optional streaming downloads.
- `fits_handler.py`: FITS validation and header-only metadata extraction.
- `storage.py`: local raw and processed metadata storage.
- `pipeline.py`: orchestration of query, product, download, and FITS stages.
- `cache.py`: deterministic query keys and optional atomic filesystem caching.
- `presets.py`: JSON target-preset validation and query conversion.

## Data flow

1. A caller creates a validated `Query` with `create_query`.
2. `IRSAClient` submits the query through PyVO.
3. PyVO returns SIA2/ObsCore records.
4. `processing.normalize_results` creates `Observation` objects.
5. `discover_products` identifies available access URLs.
6. Optional downloads are streamed by `ProductDownloader`.
7. Optional FITS metadata is extracted without loading image arrays.
8. `AstronomyPipeline` returns a structured `PipelineResult`.
9. `FileStorage` can persist raw responses or normalized metadata explicitly.

The cache is injected into `AstronomyPipeline` optionally. Without a cache,
queries follow the original direct IRSA path. Cached observation metadata is
normalized back into the same `Observation` model and does not make downloads
or storage mandatory.

## Error boundaries

Invalid caller input raises `InvalidQueryError`. Network and service failures
are translated to `IRSAConnectionError` or `IRSAResponseError`. Product and
FITS failures are represented in pipeline processing results so successful
metadata retrieval can remain available.
