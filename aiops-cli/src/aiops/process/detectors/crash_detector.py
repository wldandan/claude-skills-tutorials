"""Process crash detector."""

from typing import List
from datetime import datetime
from aiops.core import BaseDetector
from aiops.process.models import ProcessStatusMetric
from aiops.cpu.models.anomaly_event import AnomalyEvent
from aiops.core.exceptions import DetectionError


class ProcessCrashDetector(BaseDetector):
    """Detects process crashes and unexpected terminations."""

    def __init__(self, check_interval: int = 60):
        """Initialize process crash detector.

        Args:
            check_interval: Interval in seconds to check for missing processes
        """
        self.check_interval = check_interval
        self._initialized = False
        self._previous_pids = set()

    def initialize(self) -> None:
        """Initialize the detector."""
        self._initialized = True

    def detect(self, metrics: List[ProcessStatusMetric]) -> List[AnomalyEvent]:
        """Detect process crashes.

        Args:
            metrics: List of ProcessStatusMetric objects

        Returns:
            List of AnomalyEvent objects for crashed processes
        """
        if not self._initialized:
            raise DetectionError("Detector not initialized")

        events = []
        timestamp = datetime.now()

        # Get current PIDs
        current_pids = {m.pid for m in metrics}

        # Find disappeared processes
        if self._previous_pids:
            disappeared = self._previous_pids - current_pids

            if disappeared:
                import uuid
                event = AnomalyEvent(
                    id=str(uuid.uuid4()),
                    timestamp=timestamp,
                    end_time=None,
                    type='process_crash',
                    severity='critical',
                    confidence=0.8,
                    algorithm='crash_detector',
                    metrics={
                        'disappeared_count': len(disappeared),
                        'disappeared_pids': list(disappeared),
                    },
                    baseline=None,
                    top_processes=[],
                )
                events.append(event)

        # Update previous PIDs
        self._previous_pids = current_pids

        return events

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
        self._previous_pids.clear()

    def get_name(self) -> str:
        """Get detector name."""
        return 'process_crash_detector'
