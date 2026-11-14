"""Backend configuration and filesystem locations."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .exceptions import ConfigurationError


def _default_backend_directory() -> Path:
    """Return the repository's backend directory from this package location."""

    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class BackendSettings:
    """Configuration used by backend components.

    Values can be supplied through environment variables while keeping all
    default storage paths inside ``backend/``.
    """

    backend_directory: Path
    request_timeout_seconds: float
    raw_data_directory: Path
    processed_data_directory: Path

    @classmethod
    def from_environment(cls) -> "BackendSettings":
        """Build settings from environment variables and safe local defaults."""

        backend_directory = Path(
            os.getenv("ASTRONOMY_BACKEND_DIRECTORY", _default_backend_directory())
        ).expanduser()
        timeout_value = os.getenv("ASTRONOMY_REQUEST_TIMEOUT_SECONDS", "30")

        try:
            request_timeout_seconds = float(timeout_value)
        except ValueError as exc:
            raise ConfigurationError(
                "ASTRONOMY_REQUEST_TIMEOUT_SECONDS must be a number."
            ) from exc

        if request_timeout_seconds <= 0:
            raise ConfigurationError(
                "ASTRONOMY_REQUEST_TIMEOUT_SECONDS must be greater than zero."
            )

        return cls(
            backend_directory=backend_directory,
            request_timeout_seconds=request_timeout_seconds,
            raw_data_directory=backend_directory / "data" / "raw",
            processed_data_directory=backend_directory / "data" / "processed",
        )

    def ensure_data_directories(self) -> None:
        """Create configured data directories when they do not exist."""

        try:
            self.raw_data_directory.mkdir(parents=True, exist_ok=True)
            self.processed_data_directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ConfigurationError(
                f"Unable to create backend data directories: {exc}"
            ) from exc
