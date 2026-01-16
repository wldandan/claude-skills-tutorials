"""Custom exceptions for AIOps CLI."""


class AIOpsError(Exception):
    """Base exception for all AIOps errors."""

    pass


class CollectionError(AIOpsError):
    """Error during data collection."""

    pass


class DetectionError(AIOpsError):
    """Error during anomaly detection."""

    pass


class StorageError(AIOpsError):
    """Error during database operations."""

    pass


class ConfigurationError(AIOpsError):
    """Error in configuration."""

    pass


class AnalysisError(AIOpsError):
    """Error during analysis."""

    pass
