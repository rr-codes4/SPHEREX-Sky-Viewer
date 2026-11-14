"""Exceptions shared by the astronomy backend."""


class BackendError(Exception):
    """Base class for expected backend errors."""


class ConfigurationError(BackendError):
    """Raised when backend configuration is invalid."""


class InvalidQueryError(BackendError):
    """Raised when an astronomical query is invalid."""


class IRSAError(BackendError):
    """Base class for IRSA service errors."""


class IRSAConnectionError(IRSAError):
    """Raised when IRSA cannot be reached or a request times out."""


class IRSAResponseError(IRSAError):
    """Raised when IRSA returns an unusable response."""


class FITSProcessingError(BackendError):
    """Raised when a FITS file cannot be validated or inspected."""


class DownloadError(BackendError):
    """Raised when an image product cannot be downloaded safely."""


class StorageError(BackendError):
    """Raised when backend metadata cannot be stored safely."""


class CacheError(BackendError):
    """Raised when a cache entry is invalid or cannot be stored."""


class PresetValidationError(BackendError):
    """Raised when an astronomical target preset is invalid."""
