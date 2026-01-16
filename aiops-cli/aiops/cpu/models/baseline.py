"""Baseline data model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Baseline:
    """Statistical baseline for a metric."""

    metric_name: str
    window_days: int
    mean: float
    std: float
    min: float
    max: float
    percentile_95: float
    updated_at: datetime

    def get_threshold(self, multiplier: float = 2.0) -> float:
        """
        Get threshold based on baseline statistics.

        Args:
            multiplier: Number of standard deviations above mean

        Returns:
            Threshold value
        """
        return self.mean + (self.std * multiplier)
