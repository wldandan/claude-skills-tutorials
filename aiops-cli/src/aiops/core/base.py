"""Base classes for collectors, detectors, and formatters."""

from abc import ABC, abstractmethod
from typing import Any, List


class BaseCollector(ABC):
    """Abstract base class for data collectors."""

    @abstractmethod
    def collect(self) -> List[Any]:
        """
        Collect data from the system.

        Returns:
            List of collected metrics or data points
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the collector (e.g., open files, connections)."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass


class BaseDetector(ABC):
    """Abstract base class for anomaly detectors."""

    @abstractmethod
    def detect(self, metrics: List[Any]) -> List[Any]:
        """
        Detect anomalies in the provided metrics.

        Args:
            metrics: List of metric objects to analyze

        Returns:
            List of detected anomaly events
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the detector name."""
        pass


class BaseFormatter(ABC):
    """Abstract base class for output formatters."""

    @abstractmethod
    def format(self, data: Any) -> str:
        """
        Format data for output.

        Args:
            data: Data to format

        Returns:
            Formatted string
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the formatter name."""
        pass
