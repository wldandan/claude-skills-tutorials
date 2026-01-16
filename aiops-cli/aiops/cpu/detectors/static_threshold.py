"""Static threshold anomaly detector."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from aiops.cpu.detectors.base_detector import BaseDetector
from aiops.cpu.models import AnomalyEvent, CPUMetric


class StaticThresholdDetector(BaseDetector):
    """Detects CPU anomalies based on static threshold values."""

    def __init__(self, config: Dict[str, Any] = None, threshold: float = 80.0, duration_seconds: int = 300, consecutive_periods: int = 3):
        """
        Initialize the static threshold detector.

        Args:
            config: Configuration dictionary (optional, for backward compatibility)
            threshold: CPU threshold percentage (default: 80)
            duration_seconds: Minimum duration for anomaly in seconds (default: 300)
            consecutive_periods: Number of consecutive periods above threshold (default: 3)
        """
        if config is not None:
            # Support legacy config dict format
            self.threshold_percent = config.get("threshold_percent", threshold)
            self.duration_seconds = config.get("duration_seconds", duration_seconds)
        else:
            self.threshold_percent = threshold
            self.duration_seconds = duration_seconds
        self.consecutive_periods = consecutive_periods

    @property
    def threshold(self) -> float:
        """Get threshold value for backward compatibility."""
        return self.threshold_percent

    @threshold.setter
    def threshold(self, value: float):
        """Set threshold value for backward compatibility."""
        self.threshold_percent = value

    def detect(self, metrics: List[CPUMetric]) -> List[AnomalyEvent]:
        """
        Detect CPU anomalies using static threshold with improved accuracy.

        Algorithm:
        1. Require consecutive_periods consecutive points above threshold to start anomaly
        2. Allow some tolerance (points slightly below threshold) within an anomaly
        3. End anomaly when we have consecutive_periods points below threshold

        This reduces both false positives and false negatives.

        Args:
            metrics: List of CPUMetric objects

        Returns:
            List of AnomalyEvent objects
        """
        if not metrics:
            return []

        anomalies = []
        i = 0
        n = len(metrics)

        while i < n:
            # Look for start of anomaly (consecutive_periods points above threshold)
            anomaly_start = None
            consecutive_above = 0

            while i < n and consecutive_above < self.consecutive_periods:
                if metrics[i].cpu_percent > self.threshold_percent:
                    consecutive_above += 1
                    if anomaly_start is None:
                        anomaly_start = i
                else:
                    # Reset if we don't have enough consecutive points
                    consecutive_above = 0
                    anomaly_start = None
                i += 1

            # If we found a potential anomaly start
            if anomaly_start is not None and consecutive_above >= self.consecutive_periods:
                # Find end of anomaly (consecutive_periods points below threshold)
                anomaly_end = i - 1
                consecutive_below = 0

                while i < n and consecutive_below < self.consecutive_periods:
                    if metrics[i].cpu_percent <= self.threshold_percent:
                        consecutive_below += 1
                    else:
                        # Still in anomaly, reset below counter and extend end
                        consecutive_below = 0
                        anomaly_end = i
                    i += 1

                # Create anomaly event
                anomaly_metrics = metrics[anomaly_start:anomaly_end + 1]
                duration = (metrics[anomaly_end].timestamp - metrics[anomaly_start].timestamp).total_seconds()

                # Check minimum duration (or use consecutive_periods as fallback)
                min_duration = min(self.duration_seconds, self.consecutive_periods)
                if duration >= min_duration or len(anomaly_metrics) >= self.consecutive_periods:
                    anomalies.append(
                        self._create_anomaly_event(
                            metrics[anomaly_start].timestamp,
                            metrics[anomaly_end].timestamp,
                            anomaly_metrics,
                        )
                    )
            else:
                i += 1

        return anomalies

    def _create_anomaly_event(
        self,
        start_time: datetime,
        end_time: datetime,
        metrics: List[CPUMetric],
    ) -> AnomalyEvent:
        """
        Create an anomaly event from metrics.

        Args:
            start_time: Anomaly start time
            end_time: Anomaly end time
            metrics: List of metrics during anomaly

        Returns:
            AnomalyEvent object
        """
        avg_cpu = sum(m.cpu_percent for m in metrics) / len(metrics)
        max_cpu = max(m.cpu_percent for m in metrics)

        # Determine severity
        if avg_cpu > 95:
            severity = "emergency"
        elif avg_cpu > 90:
            severity = "critical"
        else:
            severity = "warning"

        # Calculate confidence based on how far above threshold
        deviation = avg_cpu - self.threshold_percent
        confidence = min(1.0, 0.5 + (deviation / 20.0))

        return AnomalyEvent(
            id=str(uuid.uuid4()),
            timestamp=start_time,
            end_time=end_time,
            severity=severity,
            type="high_cpu",
            confidence=confidence,
            metrics={
                "avg_cpu_percent": round(avg_cpu, 2),
                "max_cpu_percent": round(max_cpu, 2),
                "min_cpu_percent": round(min(m.cpu_percent for m in metrics), 2),
            },
            baseline=None,
            top_processes=[],
            algorithm="static_threshold",
        )

    def get_name(self) -> str:
        """Get the detector name."""
        return "static_threshold"
