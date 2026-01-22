"""Log volume anomaly detector."""

from typing import List
from datetime import datetime
from aiops.core import BaseDetector
from aiops.logs.models import LogEntry
from aiops.cpu.models.anomaly_event import AnomalyEvent
from aiops.core.exceptions import DetectionError


class LogVolumeAnomalyDetector(BaseDetector):
    """Detects log volume anomalies (log storms)."""

    def __init__(self, volume_threshold: int = 1000):
        """Initialize log volume anomaly detector.

        Args:
            volume_threshold: Threshold for log volume per time window
        """
        self.volume_threshold = volume_threshold
        self._initialized = False
        self._history = []

    def initialize(self) -> None:
        """Initialize the detector."""
        self._initialized = True

    def detect(self, logs: List[LogEntry]) -> List[AnomalyEvent]:
        """Detect log volume anomalies.

        Args:
            logs: List of LogEntry objects

        Returns:
            List of AnomalyEvent objects
        """
        if not self._initialized:
            raise DetectionError("Detector not initialized")

        events = []
        timestamp = datetime.now()

        # Check current volume
        current_volume = len(logs)

        if current_volume > self.volume_threshold:
            import uuid
            event = AnomalyEvent(
                id=str(uuid.uuid4()),
                timestamp=timestamp,
                end_time=None,
                type='log_storm',
                severity='warning',
                confidence=0.9,
                algorithm='log_volume_anomaly_detector',
                metrics={
                    'log_volume': current_volume,
                    'threshold': self.volume_threshold,
                    'excess_ratio': current_volume / self.volume_threshold,
                },
                baseline=self.volume_threshold,
                top_processes=[],
            )
            events.append(event)

        return events

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
        self._history.clear()

    def get_name(self) -> str:
        """Get detector name."""
        return 'log_volume_anomaly_detector'
