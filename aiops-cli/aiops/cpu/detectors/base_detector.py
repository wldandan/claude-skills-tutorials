"""Base detector class."""

from abc import ABC, abstractmethod
from typing import Any, List

from aiops.core import BaseDetector as CoreBaseDetector


class BaseDetector(CoreBaseDetector, ABC):
    """Base class for CPU anomaly detectors."""

    @abstractmethod
    def detect(self, metrics: List[Any]) -> List[Any]:
        """
        Detect anomalies in the provided metrics.

        Args:
            metrics: List of CPUMetric objects to analyze

        Returns:
            List of AnomalyEvent objects
        """
        pass
