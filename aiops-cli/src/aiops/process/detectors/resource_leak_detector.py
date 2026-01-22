"""Process resource leak detector."""

from typing import List
from datetime import datetime
import numpy as np
from aiops.core import BaseDetector
from aiops.process.models import ProcessStatusMetric
from aiops.cpu.models.anomaly_event import AnomalyEvent
from aiops.core.exceptions import DetectionError


class ResourceLeakDetector(BaseDetector):
    """Detects resource leaks (memory, file descriptors)."""

    def __init__(
        self,
        memory_growth_threshold_mb: float = 100.0,
        fd_growth_threshold: int = 100,
        min_samples: int = 10
    ):
        """Initialize resource leak detector.

        Args:
            memory_growth_threshold_mb: Memory growth threshold in MB
            fd_growth_threshold: File descriptor growth threshold
            min_samples: Minimum samples needed for detection
        """
        self.memory_growth_threshold_mb = memory_growth_threshold_mb
        self.fd_growth_threshold = fd_growth_threshold
        self.min_samples = min_samples
        self._initialized = False
        self._history = {}  # pid -> list of (timestamp, memory_rss, num_fds)

    def initialize(self) -> None:
        """Initialize the detector."""
        self._initialized = True

    def detect(self, metrics: List[ProcessStatusMetric]) -> List[AnomalyEvent]:
        """Detect resource leaks.

        Args:
            metrics: List of ProcessStatusMetric objects

        Returns:
            List of AnomalyEvent objects for resource leaks
        """
        if not self._initialized:
            raise DetectionError("Detector not initialized")

        events = []
        timestamp = datetime.now()

        # Update history
        for metric in metrics:
            if metric.pid not in self._history:
                self._history[metric.pid] = []

            self._history[metric.pid].append((
                metric.timestamp,
                metric.memory_rss,
                metric.num_fds
            ))

            # Keep only recent samples
            if len(self._history[metric.pid]) > 100:
                self._history[metric.pid] = self._history[metric.pid][-100:]

        # Detect leaks
        for metric in metrics:
            if metric.pid not in self._history:
                continue

            history = self._history[metric.pid]
            if len(history) < self.min_samples:
                continue

            # Check memory leak
            memory_values = [h[1] for h in history]
            memory_growth_mb = (memory_values[-1] - memory_values[0]) / (1024 * 1024)

            if memory_growth_mb > self.memory_growth_threshold_mb:
                import uuid
                event = AnomalyEvent(
                    id=str(uuid.uuid4()),
                    timestamp=timestamp,
                    end_time=None,
                    type='memory_leak',
                    severity='critical',
                    confidence=0.85,
                    algorithm='resource_leak_detector',
                    metrics={
                        'pid': metric.pid,
                        'process_name': metric.name,
                        'memory_growth_mb': memory_growth_mb,
                        'current_memory_mb': metric.memory_rss_mb,
                        'samples': len(history),
                    },
                    baseline=memory_values[0] / (1024 * 1024),
                    top_processes=[],
                )
                events.append(event)

            # Check file descriptor leak
            fd_values = [h[2] for h in history]
            fd_growth = fd_values[-1] - fd_values[0]

            if fd_growth > self.fd_growth_threshold:
                import uuid
                event = AnomalyEvent(
                    id=str(uuid.uuid4()),
                    timestamp=timestamp,
                    end_time=None,
                    type='fd_leak',
                    severity='warning',
                    confidence=0.80,
                    algorithm='resource_leak_detector',
                    metrics={
                        'pid': metric.pid,
                        'process_name': metric.name,
                        'fd_growth': fd_growth,
                        'current_fds': metric.num_fds,
                        'samples': len(history),
                    },
                    baseline=fd_values[0],
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
        return 'resource_leak_detector'
