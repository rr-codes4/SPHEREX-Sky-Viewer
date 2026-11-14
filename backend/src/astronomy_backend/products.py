"""Image product discovery and optional local downloading."""

from __future__ import annotations

import re
import hashlib
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlparse

import requests

from .exceptions import DownloadError
from .models import ImageProduct, Observation


def discover_products(observations: Iterable[Observation]) -> list[ImageProduct]:
    """Return products for observations that expose an access URL."""

    return [
        ImageProduct(
            observation_id=observation.observation_id,
            url=observation.access_url,
            image_format=observation.image_format,
        )
        for observation in observations
        if observation.access_url
    ]


def _safe_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return stem or "observation"


def _extension(product: ImageProduct) -> str:
    format_name = (product.image_format or "").lower()
    if "fits" in format_name or "fit" in format_name:
        return ".fits"
    suffix = Path(urlparse(product.url).path).suffix
    return suffix if suffix and len(suffix) <= 10 else ".dat"


def _validate_filename(filename: str) -> str:
    if (
        not isinstance(filename, str)
        or not filename
        or "\\" in filename
        or filename in {".", ".."}
    ):
        raise DownloadError(f"Unsafe download filename: {filename!r}")
    path = Path(filename)
    if path.name != filename:
        raise DownloadError(f"Unsafe download filename: {filename!r}")
    return filename


class ProductDownloader:
    """Stream image products into a caller-provided data directory."""

    def __init__(
        self,
        destination_directory: str | Path,
        timeout_seconds: float = 30,
        session: requests.Session | None = None,
        max_download_bytes: int | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Download timeout must be greater than zero.")
        if max_download_bytes is not None and max_download_bytes <= 0:
            raise ValueError("Maximum download size must be greater than zero.")
        self.destination_directory = Path(destination_directory).expanduser()
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.max_download_bytes = max_download_bytes

    def download(
        self,
        product: ImageProduct,
        filename: str | None = None,
    ) -> Path:
        """Download one product without overwriting an existing file."""

        parsed_url = urlparse(product.url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise DownloadError(f"Unsupported image product URL: {product.url}")

        generated_name = filename is None
        output_name = filename or (
            f"{_safe_stem(product.observation_id or 'observation')}"
            f"{_extension(product)}"
        )
        if generated_name and (self.destination_directory / output_name).exists():
            digest = hashlib.sha256(product.url.encode("utf-8")).hexdigest()[:12]
            output_name = (
                f"{_safe_stem(product.observation_id or 'observation')}"
                f"-{digest}{_extension(product)}"
            )
        output_name = _validate_filename(output_name)
        destination = self.destination_directory / output_name
        if destination.exists():
            raise DownloadError(f"Refusing to overwrite existing file: {destination}")

        try:
            self.destination_directory.mkdir(parents=True, exist_ok=True)
            with self.session.get(
                product.url,
                stream=True,
                timeout=self.timeout_seconds,
            ) as response:
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if self.max_download_bytes is not None:
                    try:
                        if (
                            content_length is not None
                            and int(content_length) > self.max_download_bytes
                        ):
                            raise DownloadError(
                                f"Image product exceeds the {self.max_download_bytes}-byte limit."
                            )
                    except (TypeError, ValueError):
                        pass
                with destination.open("xb") as output:
                    total_bytes = 0
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            total_bytes += len(chunk)
                            if (
                                self.max_download_bytes is not None
                                and total_bytes > self.max_download_bytes
                            ):
                                raise DownloadError(
                                    f"Image product exceeds the {self.max_download_bytes}-byte limit."
                                )
                            output.write(chunk)
        except DownloadError:
            try:
                destination.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        except (requests.RequestException, OSError) as exc:
            try:
                destination.unlink(missing_ok=True)
            except OSError:
                pass
            raise DownloadError(
                f"Unable to download image product to {destination}: {exc}"
            ) from exc

        return destination
