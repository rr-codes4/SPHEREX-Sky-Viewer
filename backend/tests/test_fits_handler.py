from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits
from astropy.io.fits.verify import VerifyWarning

from astronomy_backend.exceptions import FITSProcessingError
from astronomy_backend.fits_handler import read_fits_metadata, validate_fits


def _write_fits(path: Path) -> None:
    primary = fits.PrimaryHDU(data=np.zeros((2, 3), dtype=np.float32))
    primary.header["OBJECT"] = "test-target"
    primary.header["CTYPE1"] = "RA---TAN"
    primary.header["CTYPE2"] = "DEC--TAN"
    primary.header["CRVAL1"] = 12.5
    primary.header["CRVAL2"] = -4.25
    extension = fits.ImageHDU(data=np.ones((1, 2), dtype=np.int16), name="SCIENCE")
    fits.HDUList([primary, extension]).writeto(path)


def test_validate_and_read_fits_metadata_without_loading_arrays(tmp_path: Path) -> None:
    path = tmp_path / "example.fits"
    _write_fits(path)

    assert validate_fits(path) is True
    metadata = read_fits_metadata(path)

    assert metadata.path == path
    assert metadata.headers[0]["OBJECT"] == "test-target"
    assert metadata.hdu_summaries[0]["shape"] == (2, 3)
    assert metadata.hdu_summaries[1]["name"] == "SCIENCE"
    assert metadata.hdu_summaries[1]["shape"] == (1, 2)
    assert metadata.image_hdu_indices == (0, 1)
    assert metadata.wcs_metadata[0]["has_celestial"] is True
    assert all(array is None for array in metadata.arrays)

    loaded = read_fits_metadata(path, load_arrays=True)
    assert loaded.arrays[0] is not None
    assert loaded.arrays[0].shape == (2, 3)


def test_invalid_fits_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid.fits"
    path.write_text("not a FITS file", encoding="ascii")

    with pytest.raises(FITSProcessingError):
        validate_fits(path)


def test_missing_fits_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FITSProcessingError):
        read_fits_metadata(tmp_path / "missing.fits")


def test_truncated_fits_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "truncated.fits"
    _write_fits(path)
    path.write_bytes(path.read_bytes()[:100])

    with pytest.warns(VerifyWarning):
        with pytest.raises(FITSProcessingError):
            read_fits_metadata(path)
