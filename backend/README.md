# Astronomy Backend

Independent Python backend for querying astronomical image metadata through the
NASA/IPAC IRSA Simple Image Access v2 (SIA2) service.

## Features

- PyVO-based IRSA SIA2 queries.
- Astropy coordinate, unit, and time handling.
- Normalized observation models with original metadata preserved.
- Header-only FITS validation and inspection.
- Optional image-product discovery and streaming downloads.
- Safe download filenames, duplicate-name disambiguation, and optional size limits.
- Header-only FITS inspection with optional image-HDU arrays and WCS summaries.
- Optional deterministic filesystem caching with TTL, invalidation, and hit/miss statistics.
- JSON astronomical target presets with Astropy validation.
- Local storage for raw VOTable bytes and processed JSON metadata.
- Network-independent automated tests plus an opt-in live integration test.

## Installation

Python 3.11 or later is required. From the repository root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m pip install --no-deps -e backend
```

The virtual environment and generated data are ignored by
[backend/.gitignore](.gitignore).

## Basic usage

```python
import astropy.units as u

from astronomy_backend.irsa import IRSAClient, create_query

query = create_query(
    ra=269.45208 * u.deg,
    dec=4.69339 * u.deg,
    radius=6 * u.arcmin,
    collection="spherex_dr1",
)
observations = IRSAClient().search(query, max_records=10)
```

See [examples/basic_query.py](examples/basic_query.py) for a complete example.

For connecting this Python package to a JavaScript frontend, see the
[frontend integration guide](docs/frontend_integration.md). The backend does
not include an HTTP server; a small FastAPI or Flask adapter is required.

### FITS inspection

```python
from astronomy_backend.fits_handler import read_fits_metadata

metadata = read_fits_metadata("image.fits")  # header-only by default
print(metadata.image_hdu_indices, metadata.wcs_metadata)
metadata_with_arrays = read_fits_metadata("image.fits", load_arrays=True)
```

### Cache and target presets

```python
from astronomy_backend.cache import FileCache
from astronomy_backend.presets import load_presets

cache = FileCache("backend/data/cache", ttl_seconds=3600)
presets = load_presets("targets.json")
query = presets["example-target"].to_query()
```

Preset JSON uses this shape:

```json
{
  "presets": [{
    "target_id": "example-target",
    "name": "Example Target",
    "ra": 12.5,
    "dec": -4.25,
    "coordinate_unit": "deg",
    "radius": 6,
    "radius_unit": "arcmin",
    "collection": "spherex_dr1",
    "description": "Optional target description"
  }]
}
```

Units must be angular, coordinates must be valid, radius must be positive,
times must form an ordered interval, and collection identifiers are validated
locally for syntax only. Remote collection availability is not inferred.

## Tests

Run the standard suite without contacting IRSA:

```bash
PYTHONPATH=backend/src backend/.venv/bin/python -m pytest backend/tests
```

Run the optional live integration test:

```bash
RUN_IRSA_INTEGRATION=1 PYTHONPATH=backend/src \
  backend/.venv/bin/python -m pytest backend/tests/integration -m integration
```

## Configuration

The default IRSA endpoint is `https://irsa.ipac.caltech.edu/SIA`. The backend
uses a 30-second request timeout by default. Storage defaults to
`backend/data/raw/` and `backend/data/processed/`.

`ASTRONOMY_BACKEND_DIRECTORY` and
`ASTRONOMY_REQUEST_TIMEOUT_SECONDS` can override local configuration.

## Known limitations

- Query results depend on current IRSA holdings and service availability.
- The pipeline currently does not persist query responses automatically;
  `FileStorage` is available for explicit storage.
- Product downloads are never automatic during metadata searches. Downloads
  stream to local storage, refuse unsafe filenames and overwrites, and can be
  bounded with `ProductDownloader(max_download_bytes=...)`.
- Cache entries are optional, local, atomic JSON/byte files. They expire after
  the configured TTL and can be invalidated or cleared explicitly. A disabled
  cache never reads or writes entries.
- FITS processing extracts metadata only and intentionally does not analyze
  image pixels.
- No web framework or database is included.
