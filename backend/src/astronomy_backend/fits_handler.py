"""Safe, header-focused FITS validation and metadata extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits

from .exceptions import FITSProcessingError


@dataclass(frozen=True)
class FitsMetadata:
    """Metadata extracted without loading image data arrays."""

    path: Path
    headers: tuple[dict[str, Any], ...]
    hdu_summaries: tuple[dict[str, Any], ...]
    image_hdu_indices: tuple[int, ...] = ()
    wcs_metadata: tuple[dict[str, Any] | None, ...] = ()
    arrays: tuple[np.ndarray | None, ...] = ()


def _python_value(value: object) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    return value


def _open_verified(path: Path) -> fits.HDUList:
    if not path.is_file():
        raise FITSProcessingError(f"FITS file does not exist: {path}")
    try:
        hdul = fits.open(
            path,
            mode="readonly",
            memmap=True,
            lazy_load_hdus=True,
        )
        hdul.verify("exception")
        return hdul
    except (OSError, ValueError, fits.VerifyError) as exc:
        raise FITSProcessingError(f"Unable to validate FITS file {path}: {exc}") from exc


def validate_fits(path: str | Path) -> bool:
    """Validate a FITS file and return ``True`` when it is readable."""

    resolved_path = Path(path).expanduser()
    hdul = _open_verified(resolved_path)
    try:
        return True
    finally:
        hdul.close()


def read_fits_metadata(
    path: str | Path,
    *,
    load_arrays: bool = False,
) -> FitsMetadata:
    """Inspect FITS headers; load image arrays only when explicitly requested."""

    resolved_path = Path(path).expanduser()
    hdul = _open_verified(resolved_path)
    try:
        headers: list[dict[str, Any]] = []
        summaries: list[dict[str, Any]] = []
        image_indices: list[int] = []
        wcs_metadata: list[dict[str, Any] | None] = []
        arrays: list[np.ndarray | None] = []
        for index, hdu in enumerate(hdul):
            header = {
                str(key): _python_value(value)
                for key, value in hdu.header.items()
            }
            headers.append(header)
            naxis = int(header.get("NAXIS", 0) or 0)
            shape = tuple(
                int(header.get(f"NAXIS{axis}", 0) or 0)
                for axis in range(naxis, 0, -1)
            )
            summaries.append(
                {
                    "index": index,
                    "name": hdu.name,
                    "class": type(hdu).__name__,
                    "shape": shape,
                    "bitpix": header.get("BITPIX"),
                    "is_image": isinstance(hdu, (fits.PrimaryHDU, fits.ImageHDU, fits.CompImageHDU))
                    and naxis > 0,
                }
            )
            is_image = summaries[-1]["is_image"]
            if is_image:
                image_indices.append(index)
            try:
                from astropy.wcs import WCS

                wcs = WCS(hdu.header, relax=True)
                wcs_metadata.append(
                    {
                        "naxis": int(wcs.naxis),
                        "ctype": tuple(wcs.wcs.ctype),
                        "crval": tuple(float(value) for value in wcs.wcs.crval),
                        "has_celestial": bool(wcs.has_celestial),
                    }
                    if wcs.naxis
                    else None
                )
            except (ValueError, KeyError):
                wcs_metadata.append(None)
            arrays.append(np.array(hdu.data, copy=True) if load_arrays and is_image else None)
        return FitsMetadata(
            path=resolved_path,
            headers=tuple(headers),
            hdu_summaries=tuple(summaries),
            image_hdu_indices=tuple(image_indices),
            wcs_metadata=tuple(wcs_metadata),
            arrays=tuple(arrays),
        )
    except (OSError, ValueError, TypeError) as exc:
        raise FITSProcessingError(
            f"Unable to extract metadata from FITS file {resolved_path}: {exc}"
        ) from exc
    finally:
        hdul.close()
