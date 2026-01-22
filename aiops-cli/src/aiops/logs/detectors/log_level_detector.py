"""Log level anomaly detector."""

from typing import List
from datetime import datetime
from collections import Counter
from aiops.core import BaseDetector
from aiops.logs.models import LogEntry
from aiops.cpu.models.anomaly_event import AnomalyEvent
from aiops.core.exceptions import DetectionError


class LogLevelAnomalyDetector(BaseDetector):
    """Detects anomalies in log level distribution."""

    def __init__(self, error_threshold: int = 10, warning_threshold: int = 50):
        """Initialize log level anomaly detector.

        Args:
            error_threshold: Threshold for error log count
            warning_threshold: Threshold for warning log count
        """
        self.error_threshold = error_threshold
        self.warning_threshold = warning_threshold
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the detector."""
        self._initialized = True

    def detect(self, logs: List[LogEntry]) -> List[AnomalyEvent]:
        """Detect log level anomalies.

        Args:
            logs: List of LogEntry objects

        Returns:
            List of AnomalyEvent objects
        """
        if not self._initialized:
            raise DetectionError("Detector not initialized")

        events = []
        timestamp = datetime.now()

        # Count by level
        level_counts = Counter(log.level for log in logs)

        # Check error count
        error_count = sum(count for level, count in level_counts.items()
                         if level in ['ERROR', 'CRITICAL', 'FATAL'])

        if error_count > self.error_threshold:
            import uuid
            event = AnomalyEvent(
                id=str(uuid.uuid4()),
                timestamp=timestamp,
                end_time=None,
                type='high_error_rate',
                severity='critical',
                confidence=0.9,
                algorithm='log_level_anomaly_detector',
                metrics={
                    'error_count': error_count,
                    'total_logs': len(logs),
                    'error_rate': error_count / len(logs) if logs else 0,
                    'level_distribution': dict(level_counts),
                },
                baseline=self.error_threshold,
                top_processes=[],
            )
            events.append(event)

        # Check warning count
        warning_count = level_counts.get('WARNING', 0)

        if warning_count > self.warning_threshold:
            import uuid
            event = AnomalyEvent(
                id=str(uuid.uuid4()),
                timestamp=timestamp,
                end_time=None,
                type='high_warning_rate',
                severity='warning',
                confidence=0.85,
                algorithm='log_level_anomaly_detector',
                metrics={
                    'warning_count': warning_count,
                    'total_logs': len(logs),
                    'warning_rate': warning_count / len(logs) if logs else 0,
                },
                baseline=self.warning_threshold,
                top_processes=[],
            )
            events.append(event)

        return events

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False

    def get_name(self) -> str:
        """Get detector name."""
        return 'log_level_anomaly_detector'
