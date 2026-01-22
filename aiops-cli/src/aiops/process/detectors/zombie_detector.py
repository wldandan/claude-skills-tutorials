"""Zombie process detector."""

from typing import List
from datetime import datetime
from aiops.core import BaseDetector
from aiops.process.models import ProcessStatusMetric
from aiops.cpu.models.anomaly_event import AnomalyEvent
from aiops.core.exceptions import DetectionError


class ZombieProcessDetector(BaseDetector):
    """Detects zombie processes."""

    def __init__(self):
        """Initialize zombie process detector."""
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the detector."""
        self._initialized = True

    def detect(self, metrics: List[ProcessStatusMetric]) -> List[AnomalyEvent]:
        """Detect zombie processes.

        Args:
            metrics: List of ProcessStatusMetric objects

        Returns:
            List of AnomalyEvent objects for zombie processes
        """
        if not self._initialized:
            raise DetectionError("Detector not initialized")

        events = []
        timestamp = datetime.now()

        # Find zombie processes
        zombies = [m for m in metrics if m.is_zombie]

        if zombies:
            # Create anomaly event
            import uuid
            event = AnomalyEvent(
                id=str(uuid.uuid4()),
                timestamp=timestamp,
                end_time=None,
                type='zombie_process',
                severity='warning',
                confidence=1.0,
                algorithm='zombie_detector',
                metrics={
                    'zombie_count': len(zombies),
                    'zombie_pids': [z.pid for z in zombies],
                    'zombie_names': [z.name for z in zombies],
                    'parent_pids': [z.ppid for z in zombies],
                },
                baseline=None,
                top_processes=[],
            )
            events.append(event)

        return events

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False

    def get_name(self) -> str:
        """Get detector name."""
        return 'zombie_process_detector'
