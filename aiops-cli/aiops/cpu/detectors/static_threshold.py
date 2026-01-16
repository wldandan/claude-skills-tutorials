"""Static threshold anomaly detector."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from aiops.cpu.detectors.base_detector import BaseDetector
from aiops.cpu.models import AnomalyEvent, CPUMetric


class StaticThresholdDetector(BaseDetector):
    """Detects CPU anomalies based on static threshold values."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the static threshold detector.

        Args:
            config: Configuration dictionary with keys:
                - threshold_percent: CPU threshold (default: 80)
                - duration_seconds: Minimum duration for anomaly (default: 300)
        """
        self.threshold_percent = config.get("threshold_percent", 80.0)
        self.duration_seconds = config.get("duration_seconds", 300)

    def detect(self, metrics: List[CPUMetric]) -> List[AnomalyEvent]:
        """
        Detect CPU anomalies using static threshold.

        Args:
            metrics: List of CPUMetric objects

        Returns:
            List of AnomalyEvent objects
        """
        if not metrics:
            return []

        anomalies = []
        current_anomaly_start = None
        anomaly_metrics = []

        for metric in metrics:
            if metric.cpu_percent > self.threshold_percent:
                if current_anomaly_start is None:
                    # Start of potential anomaly
                    current_anomaly_start = metric.timestamp
                    anomaly_metrics = [metric]
                else:
                    # Continuation of anomaly
                    anomaly_metrics.append(metric)
            else:
                # CPU below threshold
                if current_anomaly_start is not None:
                    # Check if anomaly lasted long enough
                    duration = (metric.timestamp - current_anomaly_start).total_seconds()
                    if duration >= self.duration_seconds:
                        anomalies.append(
                            self._create_anomaly_event(
                                current_anomaly_start,
                                metric.timestamp,
                                anomaly_metrics,
                            )
                        )
                    # Reset
                    current_anomaly_start = None
                    anomaly_metrics = []

        # Handle case where data ends while anomaly is ongoing
        if current_anomaly_start is not None:
            duration = (metrics[-1].timestamp - current_anomaly_start).total_seconds()
            if duration >= self.duration_seconds:
                anomalies.append(
                    self._create_anomaly_event(
                        current_anomaly_start,
                        metrics[-1].timestamp,
                        anomaly_metrics,
                    )
                )

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
