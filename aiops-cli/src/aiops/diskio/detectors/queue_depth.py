"""Queue depth anomaly detector.

Detects abnormal I/O queue depths indicating I/O congestion.
"""

import uuid
from datetime import datetime
from typing import List, Optional
import numpy as np

from aiops.core import BaseDetector
from aiops.diskio.models import DiskIOMetric
from aiops.cpu.models.anomaly_event import AnomalyEvent


class QueueDepthDetector(BaseDetector):
    """Detects queue depth anomalies indicating I/O congestion."""

    def __init__(
        self,
        queue_threshold: int = 10,
        sustained_duration_ratio: float = 0.3,
        min_samples: int = 10,
        confidence_threshold: float = 0.7,
    ):
        """Initialize queue depth detector.

        Args:
            queue_threshold: Queue depth threshold for anomaly
            sustained_duration_ratio: Ratio of samples above threshold to consider sustained
            min_samples: Minimum samples required for detection
            confidence_threshold: Minimum confidence for anomaly detection
        """
        self.queue_threshold = queue_threshold
        self.sustained_duration_ratio = sustained_duration_ratio
        self.min_samples = min_samples
        self.confidence_threshold = confidence_threshold

    def detect(self, metrics: List[DiskIOMetric]) -> List[AnomalyEvent]:
        """Detect queue depth anomalies.

        Args:
            metrics: List of DiskIOMetric objects

        Returns:
            List of AnomalyEvent objects
        """
        if len(metrics) < self.min_samples:
            return []

        # Group metrics by device
        device_metrics = {}
        for metric in metrics:
            if metric.device not in device_metrics:
                device_metrics[metric.device] = []
            device_metrics[metric.device].append(metric)

        anomalies = []
        for device, dev_metrics in device_metrics.items():
            device_anomaly = self._detect_device_queue_depth(device, dev_metrics)
            if device_anomaly:
                anomalies.append(device_anomaly)

        return anomalies

    def _detect_device_queue_depth(
        self, device: str, metrics: List[DiskIOMetric]
    ) -> Optional[AnomalyEvent]:
        """Detect queue depth anomalies for a specific device.

        Args:
            device: Device name
            metrics: List of metrics for this device

        Returns:
            AnomalyEvent if anomaly detected, None otherwise
        """
        if len(metrics) < self.min_samples:
            return None

        # Extract queue depths and timestamps
        queue_depths = []
        timestamps = []

        for metric in metrics:
            timestamps.append(metric.timestamp)
            queue_depths.append(metric.io_in_progress)

        queue_depths = np.array(queue_depths)

        # Calculate baseline (median)
        baseline = np.median(queue_depths)

        # Find high queue depth periods
        high_queue_indices = np.where(queue_depths > self.queue_threshold)[0]

        if len(high_queue_indices) == 0:
            return None

        # Check if sustained
        high_queue_ratio = len(high_queue_indices) / len(queue_depths)

        if high_queue_ratio < self.sustained_duration_ratio:
            return None

        # Calculate confidence
        max_queue_depth = queue_depths[high_queue_indices].max()
        avg_queue_depth = queue_depths[high_queue_indices].mean()

        # Confidence based on duration and magnitude
        confidence = min(
            0.5
            + (high_queue_ratio * 0.3)
            + (min(max_queue_depth / (self.queue_threshold * 2), 1.0) * 0.2),
            1.0,
        )

        if confidence < self.confidence_threshold:
            return None

        # Determine severity
        if max_queue_depth >= 50 or high_queue_ratio >= 0.7:
            severity = "critical"
        elif max_queue_depth >= 20 or high_queue_ratio >= 0.5:
            severity = "warning"
        else:
            severity = "warning"  # Changed from "info" to "warning"

        # Create anomaly event
        event_id = str(uuid.uuid4())
        timestamp = timestamps[high_queue_indices[0]]

        return AnomalyEvent(
            id=event_id,
            timestamp=timestamp,
            end_time=None,
            type="io_queue_congestion",
            severity=severity,
            confidence=confidence,
            algorithm="threshold_sustained",
            baseline=float(baseline),
            top_processes=[],
            metrics={
                "device": device,
                "baseline_queue_depth": float(baseline),
                "max_queue_depth": int(max_queue_depth),
                "avg_high_queue_depth": float(avg_queue_depth),
                "high_queue_count": int(len(high_queue_indices)),
                "high_queue_ratio": float(high_queue_ratio),
                "threshold": self.queue_threshold,
            },
        )

    def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    def get_name(self) -> str:
        """Return detector name.

        Returns:
            'queue_depth'
        """
        return 'queue_depth'
