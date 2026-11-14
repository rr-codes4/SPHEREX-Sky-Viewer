# API reference

## Querying

`astronomy_backend.irsa.create_query(ra, dec, radius, collection=None, frame="icrs")`
validates angular inputs and transforms supported equatorial frames to ICRS.
Numeric values are interpreted as degrees; Astropy `Quantity` values preserve
explicit units.

`IRSAClient(service_url=..., timeout_seconds=30).search(query, max_records=100)`
returns `list[Observation]`. An empty list is a valid response.

## Models

- `Query`: ICRS coordinates, angular radius, optional collection, and timestamp.
- `Observation`: normalized ObsCore metadata and original source metadata.
- `ImageProduct`: observation identifier, access URL, and image format.
- `ProcessingResult`: per-observation download/FITS outcome.
- `PipelineResult`: overall pipeline status, observations, products, and errors.

## Processing

`normalize_observation(row)` converts one mapping of VOTable fields into an
`Observation`. `normalize_results(rows)` applies it to an iterable of rows.

`validate_fits(path)` validates a FITS file. `read_fits_metadata(path)` returns
headers, image-HDU indices, and WCS summaries without loading image arrays by
default. Pass `load_arrays=True` only when arrays are explicitly required.

## Cache and presets

`query_cache_key(query)` creates a deterministic key from normalized spatial,
collection, time, and extra query parameters. `FileCache` supports JSON/bytes
lookup, TTL expiration, invalidation, clearing, atomic writes, and hit/miss
statistics.

`validate_preset(data)` validates one target object. `load_presets(path)` loads
a JSON list or `{ "presets": [...] }`, rejects malformed data and duplicate
target IDs, and returns `TargetPreset` objects. `TargetPreset.to_query()`
converts valid data to the existing `Query` model.

## Storage and downloads

`discover_products(observations)` returns products with access URLs.
`ProductDownloader(destination_directory).download(product)` streams one
product and refuses to overwrite an existing file.

`FileStorage.save_raw_votable(content, filename)` stores raw bytes.
`FileStorage.save_processed_metadata(metadata, filename)` stores normalized
JSON. Both methods reject unsafe filenames and overwrites.

## Exceptions

`InvalidQueryError`, `IRSAConnectionError`, `IRSAResponseError`,
`FITSProcessingError`, `DownloadError`, and `StorageError` provide explicit
failure categories.
