"""IO latency anomaly detector.

Detects sudden increases in disk I/O latency (await time).
"""

import uuid
from datetime import datetime
from typing import List, Optional
import numpy as np
from scipy import stats

from aiops.core import BaseDetector
from aiops.diskio.models import DiskIOMetric
from aiops.cpu.models.anomaly_event import AnomalyEvent


class IOLatencyDetector(BaseDetector):
    """Detects IO latency anomalies using threshold and statistical methods."""

    def __init__(
        self,
        latency_threshold_ms: float = 100.0,
        spike_multiplier: float = 3.0,
        min_samples: int = 10,
        confidence_threshold: float = 0.7,
    ):
        """Initialize IO latency detector.

        Args:
            latency_threshold_ms: Absolute latency threshold in milliseconds
            spike_multiplier: Multiplier for baseline to detect spikes
            min_samples: Minimum samples required for detection
            confidence_threshold: Minimum confidence for anomaly detection
        """
        self.latency_threshold_ms = latency_threshold_ms
        self.spike_multiplier = spike_multiplier
        self.min_samples = min_samples
        self.confidence_threshold = confidence_threshold

    def detect(self, metrics: List[DiskIOMetric]) -> List[AnomalyEvent]:
        """Detect IO latency anomalies.

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
            device_anomalies = self._detect_device_latency(device, dev_metrics)
            anomalies.extend(device_anomalies)

        return anomalies

    def _detect_device_latency(
        self, device: str, metrics: List[DiskIOMetric]
    ) -> List[AnomalyEvent]:
        """Detect latency anomalies for a specific device.

        Args:
            device: Device name
            metrics: List of metrics for this device

        Returns:
            List of AnomalyEvent objects
        """
        if len(metrics) < self.min_samples:
            return []

        # Extract latency values
        read_latencies = []
        write_latencies = []
        timestamps = []

        for metric in metrics:
            timestamps.append(metric.timestamp)
            read_latencies.append(metric.avg_read_time_ms)
            write_latencies.append(metric.avg_write_time_ms)

        read_latencies = np.array(read_latencies)
        write_latencies = np.array(write_latencies)

        anomalies = []

        # Detect read latency anomalies
        read_anomaly = self._detect_latency_spike(
            timestamps, read_latencies, "read", device
        )
        if read_anomaly:
            anomalies.append(read_anomaly)

        # Detect write latency anomalies
        write_anomaly = self._detect_latency_spike(
            timestamps, write_latencies, "write", device
        )
        if write_anomaly:
            anomalies.append(write_anomaly)

        return anomalies

    def _detect_latency_spike(
        self,
        timestamps: List[datetime],
        latencies: np.ndarray,
        io_type: str,
        device: str,
    ) -> Optional[AnomalyEvent]:
        """Detect latency spike using threshold and statistical methods.

        Args:
            timestamps: List of timestamps
            latencies: Array of latency values
            io_type: Type of IO ("read" or "write")
            device: Device name

        Returns:
            AnomalyEvent if anomaly detected, None otherwise
        """
        # Calculate baseline (median of lower 50%)
        baseline = np.median(np.sort(latencies)[: len(latencies) // 2])

        # Find spikes
        spike_threshold = max(
            self.latency_threshold_ms, baseline * self.spike_multiplier
        )
        spike_indices = np.where(latencies > spike_threshold)[0]

        if len(spike_indices) == 0:
            return None

        # Calculate confidence based on spike magnitude and frequency
        max_latency = latencies[spike_indices].max()
        spike_ratio = len(spike_indices) / len(latencies)
        magnitude_ratio = max_latency / baseline if baseline > 0 else float('inf')

        # Confidence: higher for more frequent and larger spikes
        confidence = min(
            0.5 + (spike_ratio * 0.3) + (min(magnitude_ratio / 10, 1.0) * 0.2), 1.0
        )

        if confidence < self.confidence_threshold:
            return None

        # Determine severity
        if max_latency >= 500 or magnitude_ratio >= 10:
            severity = "critical"
        elif max_latency >= 200 or magnitude_ratio >= 5:
            severity = "warning"
        else:
            severity = "warning"  # Changed from "info" to "warning"

        # Create anomaly event
        event_id = str(uuid.uuid4())
        timestamp = timestamps[spike_indices[0]]

        return AnomalyEvent(
            id=event_id,
            timestamp=timestamp,
            end_time=None,
            type=f"io_latency_spike_{io_type}",
            severity=severity,
            confidence=confidence,
            algorithm="threshold_statistical",
            baseline=float(baseline),
            top_processes=[],
            metrics={
                "device": device,
                "io_type": io_type,
                "baseline_latency_ms": float(baseline),
                "max_latency_ms": float(max_latency),
                "avg_spike_latency_ms": float(latencies[spike_indices].mean()),
                "spike_count": int(len(spike_indices)),
                "spike_ratio": float(spike_ratio),
                "magnitude_ratio": float(magnitude_ratio),
            },
        )

    def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    def get_name(self) -> str:
        """Return detector name.

        Returns:
            'io_latency'
        """
        return 'io_latency'
