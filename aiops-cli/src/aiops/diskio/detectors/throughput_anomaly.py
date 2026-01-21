"""Throughput anomaly detector.

Detects sudden drops or spikes in disk I/O throughput.
"""

import uuid
from datetime import datetime
from typing import List, Optional
import numpy as np
from scipy import stats

from aiops.core import BaseDetector
from aiops.diskio.models import DiskIOMetric
from aiops.cpu.models.anomaly_event import AnomalyEvent


class ThroughputAnomalyDetector(BaseDetector):
    """Detects throughput anomalies using statistical methods."""

    def __init__(
        self,
        drop_threshold_percent: float = 50.0,
        spike_multiplier: float = 3.0,
        min_samples: int = 10,
        confidence_threshold: float = 0.7,
    ):
        """Initialize throughput anomaly detector.

        Args:
            drop_threshold_percent: Percentage drop to consider anomalous
            spike_multiplier: Multiplier for baseline to detect spikes
            min_samples: Minimum samples required for detection
            confidence_threshold: Minimum confidence for anomaly detection
        """
        self.drop_threshold_percent = drop_threshold_percent
        self.spike_multiplier = spike_multiplier
        self.min_samples = min_samples
        self.confidence_threshold = confidence_threshold

    def detect(self, metrics: List[DiskIOMetric]) -> List[AnomalyEvent]:
        """Detect throughput anomalies.

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
            device_anomalies = self._detect_device_throughput(device, dev_metrics)
            anomalies.extend(device_anomalies)

        return anomalies

    def _detect_device_throughput(
        self, device: str, metrics: List[DiskIOMetric]
    ) -> List[AnomalyEvent]:
        """Detect throughput anomalies for a specific device.

        Args:
            device: Device name
            metrics: List of metrics for this device

        Returns:
            List of AnomalyEvent objects
        """
        if len(metrics) < self.min_samples:
            return []

        # Calculate throughput (bytes per second)
        # Note: We need time intervals between metrics for accurate throughput
        # For simplicity, we'll use the raw byte counts as proxy
        read_throughputs = []
        write_throughputs = []
        timestamps = []

        for metric in metrics:
            timestamps.append(metric.timestamp)
            read_throughputs.append(metric.read_bytes)
            write_throughputs.append(metric.write_bytes)

        read_throughputs = np.array(read_throughputs)
        write_throughputs = np.array(write_throughputs)

        anomalies = []

        # Detect read throughput anomalies
        read_drop = self._detect_throughput_drop(
            timestamps, read_throughputs, "read", device
        )
        if read_drop:
            anomalies.append(read_drop)

        read_spike = self._detect_throughput_spike(
            timestamps, read_throughputs, "read", device
        )
        if read_spike:
            anomalies.append(read_spike)

        # Detect write throughput anomalies
        write_drop = self._detect_throughput_drop(
            timestamps, write_throughputs, "write", device
        )
        if write_drop:
            anomalies.append(write_drop)

        write_spike = self._detect_throughput_spike(
            timestamps, write_throughputs, "write", device
        )
        if write_spike:
            anomalies.append(write_spike)

        return anomalies

    def _detect_throughput_drop(
        self,
        timestamps: List[datetime],
        throughputs: np.ndarray,
        io_type: str,
        device: str,
    ) -> Optional[AnomalyEvent]:
        """Detect throughput drop.

        Args:
            timestamps: List of timestamps
            throughputs: Array of throughput values
            io_type: Type of IO ("read" or "write")
            device: Device name

        Returns:
            AnomalyEvent if anomaly detected, None otherwise
        """
        # Calculate baseline (median of upper 50%)
        baseline = np.median(np.sort(throughputs)[len(throughputs) // 2 :])

        if baseline == 0:
            return None

        # Find drops
        drop_threshold = baseline * (1 - self.drop_threshold_percent / 100)
        drop_indices = np.where(throughputs < drop_threshold)[0]

        if len(drop_indices) == 0:
            return None

        # Calculate confidence
        min_throughput = throughputs[drop_indices].min()
        drop_ratio = len(drop_indices) / len(throughputs)
        magnitude_ratio = (baseline - min_throughput) / baseline

        confidence = min(0.5 + (drop_ratio * 0.3) + (magnitude_ratio * 0.2), 1.0)

        if confidence < self.confidence_threshold:
            return None

        # Determine severity
        if magnitude_ratio >= 0.8:  # 80% drop
            severity = "critical"
        elif magnitude_ratio >= 0.5:  # 50% drop
            severity = "warning"
        else:
            severity = "warning"  # Changed from "info" to "warning"

        # Create anomaly event
        event_id = str(uuid.uuid4())
        timestamp = timestamps[drop_indices[0]]

        return AnomalyEvent(
            id=event_id,
            timestamp=timestamp,
            end_time=None,
            type=f"throughput_drop_{io_type}",
            severity=severity,
            confidence=confidence,
            algorithm="statistical_threshold",
            baseline=float(baseline),
            top_processes=[],
            metrics={
                "device": device,
                "io_type": io_type,
                "baseline_throughput_bytes": float(baseline),
                "min_throughput_bytes": float(min_throughput),
                "avg_drop_throughput_bytes": float(throughputs[drop_indices].mean()),
                "drop_count": int(len(drop_indices)),
                "drop_ratio": float(drop_ratio),
                "magnitude_ratio": float(magnitude_ratio),
            },
        )

    def _detect_throughput_spike(
        self,
        timestamps: List[datetime],
        throughputs: np.ndarray,
        io_type: str,
        device: str,
    ) -> Optional[AnomalyEvent]:
        """Detect throughput spike (abnormally high).

        Args:
            timestamps: List of timestamps
            throughputs: Array of throughput values
            io_type: Type of IO ("read" or "write")
            device: Device name

        Returns:
            AnomalyEvent if anomaly detected, None otherwise
        """
        # Calculate baseline (median)
        baseline = np.median(throughputs)

        if baseline == 0:
            return None

        # Find spikes
        spike_threshold = baseline * self.spike_multiplier
        spike_indices = np.where(throughputs > spike_threshold)[0]

        if len(spike_indices) == 0:
            return None

        # Calculate confidence
        max_throughput = throughputs[spike_indices].max()
        spike_ratio = len(spike_indices) / len(throughputs)
        magnitude_ratio = max_throughput / baseline

        confidence = min(
            0.5 + (spike_ratio * 0.3) + (min(magnitude_ratio / 10, 1.0) * 0.2), 1.0
        )

        if confidence < self.confidence_threshold:
            return None

        # Determine severity (spikes are usually less critical than drops)
        if magnitude_ratio >= 10:
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
            type=f"throughput_spike_{io_type}",
            severity=severity,
            confidence=confidence,
            algorithm="statistical_threshold",
            baseline=float(baseline),
            top_processes=[],
            metrics={
                "device": device,
                "io_type": io_type,
                "baseline_throughput_bytes": float(baseline),
                "max_throughput_bytes": float(max_throughput),
                "avg_spike_throughput_bytes": float(throughputs[spike_indices].mean()),
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
            'throughput_anomaly'
        """
        return 'throughput_anomaly'
