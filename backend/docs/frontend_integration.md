# Frontend Integration Guide

## Important: the backend is not currently an HTTP API

The backend is a Python package. It does not include Flask, FastAPI, Django, a
database, or any web routes. A browser cannot import
`astronomy_backend` directly.

To connect a JavaScript frontend, add a small HTTP adapter in front of the
package. The adapter receives JSON from the browser, calls the existing
Python pipeline, and returns JSON-safe data. The frontend then calls that
adapter with `fetch()` or another HTTP client.

```text
Browser frontend
    │ JSON over HTTP
    ▼
HTTP adapter (FastAPI/Flask)
    │ Python calls
    ▼
AstronomyPipeline
    │
    ├── IRSA SIA2 metadata service
    ├── optional local cache
    ├── optional product downloads
    └── optional FITS inspection
```

The current repository does not contain a frontend source directory or an HTTP
adapter. The examples below are an integration pattern, not an already
available endpoint.

## 1. Install an HTTP framework

Keep the astronomy package dependencies in
[`pyproject.toml`](../pyproject.toml), and add the adapter's framework to the
backend environment:

```bash
backend/.venv/bin/python -m pip install fastapi uvicorn
```

For a committed deployment, add the chosen framework to the project's
dependency manifest rather than relying on a one-off installation.

## 2. Create a minimal API adapter

Create an application file outside the package, for example
`backend/api.py`. This adapter should:

1. Validate the incoming JSON.
2. Build a `Query` with `create_query()`.
3. Run `AstronomyPipeline`.
4. Convert Astropy and dataclass values into JSON-safe values.
5. Return the pipeline status and errors without hiding failures.

Example:

```python
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import astropy.units as u

from astronomy_backend.cache import FileCache
from astronomy_backend.exceptions import InvalidQueryError
from astronomy_backend.irsa import IRSAClient, create_query
from astronomy_backend.pipeline import AstronomyPipeline


class SearchRequest(BaseModel):
    ra: float = Field(ge=0, lt=360)
    dec: float = Field(ge=-90, le=90)
    radius_arcmin: float = Field(gt=0, le=5400)
    collection: str | None = None
    max_records: int = Field(default=100, ge=0, le=1000)


app = FastAPI(title="SPHEREx Sky Viewer API")

# Replace this with the exact deployed frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

pipeline = AstronomyPipeline(
    IRSAClient(),
    cache=FileCache("backend/data/cache", ttl_seconds=3600),
)


def observation_to_json(observation: Any) -> dict[str, Any]:
    coordinates = observation.coordinates
    observation_time = observation.observation_time
    return {
        "observation_id": observation.observation_id,
        "ra": coordinates.icrs.ra.deg if coordinates else None,
        "dec": coordinates.icrs.dec.deg if coordinates else None,
        "instrument": observation.instrument,
        "collection": observation.collection,
        "observation_time": observation_time.isot
        if observation_time
        else None,
        "exposure_seconds": observation.exposure_seconds,
        "access_url": observation.access_url,
        "image_format": observation.image_format,
        "original_metadata": observation.original_metadata,
    }


@app.post("/api/search")
def search(request: SearchRequest) -> dict[str, Any]:
    try:
        query = create_query(
            request.ra,
            request.dec,
            request.radius_arcmin * u.arcmin,
            collection=request.collection,
        )
        result = pipeline.run(query, max_records=request.max_records)
    except InvalidQueryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "status": result.status,
        "query": {
            "ra": query.coordinates.icrs.ra.deg,
            "dec": query.coordinates.icrs.dec.deg,
            "radius_degrees": query.radius_degrees,
            "collection": query.collection,
        },
        "observations": [
            observation_to_json(observation)
            for observation in result.observations
        ],
        "errors": list(result.errors),
    }
```

The example deliberately returns metadata URLs rather than proxying image
bytes through the API. The browser can use those URLs only when IRSA permits
browser access; otherwise add a dedicated, bounded download endpoint in the
adapter and keep downloaded files outside the public web root.

## 3. Start the adapter

From the repository root:

```bash
PYTHONPATH=backend/src backend/.venv/bin/uvicorn api:app \
  --app-dir backend --reload --host 127.0.0.1 --port 8000
```

The endpoint is now:

```text
POST http://127.0.0.1:8000/api/search
```

The interactive API description is available at
`http://127.0.0.1:8000/docs`.

## 4. Call it from the frontend

The frontend sends JSON using the field names defined by `SearchRequest`:

```javascript
export async function searchSky({ ra, dec, radiusArcmin, collection }) {
  const response = await fetch("http://127.0.0.1:8000/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ra,
      dec,
      radius_arcmin: radiusArcmin,
      collection: collection || null,
      max_records: 100,
    }),
  });

  const payload = await response.json();
  if (!response.ok) {
    const message =
      typeof payload.detail === "string"
        ? payload.detail
        : "Astronomy search failed.";
    throw new Error(message);
  }
  return payload;
}
```

Example response:

```json
{
  "status": "success",
  "query": {
    "ra": 269.45208,
    "dec": 4.69339,
    "radius_degrees": 0.1,
    "collection": "spherex_dr1"
  },
  "observations": [
    {
      "observation_id": "example-id",
      "ra": 269.45,
      "dec": 4.69,
      "instrument": "example-instrument",
      "collection": "spherex_dr1",
      "observation_time": "2025-01-01T00:00:00.000",
      "exposure_seconds": 10.0,
      "access_url": "https://example.test/image.fits",
      "image_format": "image/fits",
      "original_metadata": {}
    }
  ],
  "errors": []
}
```

The UI should handle these pipeline statuses:

- `success`: observations are available.
- `empty`: the query succeeded but returned no observations.
- `partial`: metadata succeeded, but an optional download or FITS operation
  failed; show the observations and the errors.
- `invalid_query`: the submitted query is invalid.
- `query_failed`: IRSA could not be reached or returned an unusable response.

Do not treat an empty observation list as a server failure.

## 5. Displaying images and FITS products

The metadata search does not download products automatically. A frontend
typically needs a second operation for products:

1. Search for observations.
2. Display metadata and available `access_url` values.
3. Ask the user to select a product or frame.
4. Send that selection to a server-side download endpoint.
5. Return a safe local asset URL or stream the file.
6. If needed, run `read_fits_metadata()` server-side and return only the
   selected headers, WCS summary, or a deliberately requested array.

Do not accept arbitrary filesystem paths from the browser. Use an observation
identifier or server-issued product token, validate the remote URL, enforce a
download size limit, and never overwrite existing files. These protections are
already implemented by `ProductDownloader` and should be preserved by the
adapter.

FITS arrays can be large. Keep `load_arrays=False` unless the frontend
explicitly needs pixel data, and consider returning a resized or tiled image
format instead of raw NumPy arrays.

## 6. Environment configuration

Configure the adapter process with:

```bash
export ASTRONOMY_BACKEND_DIRECTORY=/absolute/path/to/repository/backend
export ASTRONOMY_REQUEST_TIMEOUT_SECONDS=30
```

The backend uses these local directories by default:

```text
backend/data/raw/
backend/data/processed/
backend/data/cache/
```

Ensure the API process can write to directories used for cache, downloads, and
explicit storage. Do not commit generated data or downloaded FITS files.

## 7. Development and production checklist

### Local development

- Run the Python API on `127.0.0.1:8000`.
- Run the frontend development server on its own port.
- Set CORS to the exact frontend origin.
- Test invalid coordinates, empty results, IRSA outages, and malformed input.
- Use the backend's network-independent tests before live integration tests.

### Production

- Put the frontend and API behind HTTPS.
- Restrict CORS to the deployed frontend origin; never use `*` casually.
- Keep IRSA credentials and server configuration out of browser code.
- Add authentication and rate limiting if the API is public.
- Enforce maximum records, download sizes, request timeouts, and response
  limits.
- Store downloads outside the public directory and serve only approved files.
- Add structured logging and monitoring for IRSA failures and slow requests.
- Run multiple API workers only after confirming that local cache and storage
  behavior is appropriate for the deployment.

## 8. Alternative architecture: server-side frontend

If the frontend uses a Python server-rendered framework, it can call
`astronomy_backend` directly without an HTTP hop between the UI and backend.
The same rules still apply:

- Validate user input with `create_query()`.
- Convert Astropy objects before rendering or serializing.
- Keep IRSA calls and filesystem access on the server.
- Do not expose local paths or unrestricted download URLs.
- Preserve explicit backend error categories for user-facing messages.

