"""Swap anomaly detector for detecting swap usage spikes."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np

from aiops.core import BaseDetector
from aiops.cpu.models import AnomalyEvent
from aiops.memory.models import MemoryMetric


class SwapAnomalyDetector(BaseDetector):
    """Detects swap usage anomalies including spikes and sustained high usage."""

    def __init__(
        self,
        threshold_percent: float = 10.0,
        spike_multiplier: float = 2.0,
        min_samples: int = 10,
    ):
        """
        Initialize the swap anomaly detector.

        Args:
            threshold_percent: Swap usage threshold percentage (default: 10.0)
            spike_multiplier: Multiplier for spike detection (default: 2.0)
            min_samples: Minimum number of samples required (default: 10)
        """
        self.threshold_percent = threshold_percent
        self.spike_multiplier = spike_multiplier
        self.min_samples = min_samples

    def detect(self, metrics: List[MemoryMetric]) -> List[AnomalyEvent]:
        """
        Detect swap usage anomalies.

        Algorithm:
        1. Calculate baseline swap usage (mean and std dev)
        2. Detect sudden spikes (> spike_multiplier * baseline)
        3. Detect sustained high usage (> threshold_percent)
        4. Generate alerts for both types of anomalies

        Args:
            metrics: List of MemoryMetric objects

        Returns:
            List of AnomalyEvent objects for detected swap anomalies
        """
        if not metrics or len(metrics) < self.min_samples:
            return []

        # Sort metrics by timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)

        anomalies = []

        # Detect sustained high swap usage
        high_usage_events = self._detect_sustained_high_usage(sorted_metrics)
        anomalies.extend(high_usage_events)

        # Detect swap spikes
        spike_events = self._detect_swap_spikes(sorted_metrics)
        anomalies.extend(spike_events)

        return anomalies

    def _detect_sustained_high_usage(
        self, metrics: List[MemoryMetric]
    ) -> List[AnomalyEvent]:
        """
        Detect sustained high swap usage.

        Args:
            metrics: Sorted list of MemoryMetric objects

        Returns:
            List of AnomalyEvent objects
        """
        anomalies = []
        in_anomaly = False
        anomaly_start_idx = None

        for i, metric in enumerate(metrics):
            if metric.swap_used_percent > self.threshold_percent:
                if not in_anomaly:
                    # Start of anomaly
                    in_anomaly = True
                    anomaly_start_idx = i
            else:
                if in_anomaly:
                    # End of anomaly
                    anomaly_metrics = metrics[anomaly_start_idx:i]
                    if len(anomaly_metrics) >= 3:  # Require at least 3 points
                        anomalies.append(
                            self._create_sustained_usage_event(anomaly_metrics)
                        )
                    in_anomaly = False
                    anomaly_start_idx = None

        # Handle case where anomaly extends to end of data
        if in_anomaly and anomaly_start_idx is not None:
            anomaly_metrics = metrics[anomaly_start_idx:]
            if len(anomaly_metrics) >= 3:
                anomalies.append(self._create_sustained_usage_event(anomaly_metrics))

        return anomalies

    def _detect_swap_spikes(self, metrics: List[MemoryMetric]) -> List[AnomalyEvent]:
        """
        Detect sudden swap usage spikes.

        Args:
            metrics: Sorted list of MemoryMetric objects

        Returns:
            List of AnomalyEvent objects
        """
        if len(metrics) < self.min_samples:
            return []

        # Calculate baseline (mean and std dev of first half)
        baseline_size = len(metrics) // 2
        baseline_metrics = metrics[:baseline_size]
        baseline_swap = np.array([m.swap_used_percent for m in baseline_metrics])
        baseline_mean = np.mean(baseline_swap)
        baseline_std = np.std(baseline_swap)

        # Detect spikes in second half
        anomalies = []
        spike_threshold = baseline_mean + (self.spike_multiplier * baseline_std)

        for i in range(baseline_size, len(metrics)):
            metric = metrics[i]
            if metric.swap_used_percent > spike_threshold:
                # Found a spike
                anomalies.append(
                    self._create_spike_event(
                        metric, baseline_mean, spike_threshold
                    )
                )

        return anomalies

    def _create_sustained_usage_event(
        self, metrics: List[MemoryMetric]
    ) -> AnomalyEvent:
        """
        Create an anomaly event for sustained high swap usage.

        Args:
            metrics: List of metrics during anomaly

        Returns:
            AnomalyEvent object
        """
        start_time = metrics[0].timestamp
        end_time = metrics[-1].timestamp

        # Calculate statistics
        avg_swap = sum(m.swap_used_percent for m in metrics) / len(metrics)
        max_swap = max(m.swap_used_percent for m in metrics)
        min_swap = min(m.swap_used_percent for m in metrics)

        # Calculate severity
        severity = self._calculate_severity(avg_swap)

        # Calculate confidence based on consistency
        swap_values = [m.swap_used_percent for m in metrics]
        consistency = 1.0 - (np.std(swap_values) / (np.mean(swap_values) + 1e-6))
        confidence = min(1.0, max(0.5, consistency))

        # Get swap statistics from last metric
        last_metric = metrics[-1]
        swap_total_gb = last_metric.swap_total / (1024 ** 3)
        swap_used_gb = last_metric.swap_used / (1024 ** 3)

        event_metrics = {
            "avg_swap_percent": round(avg_swap, 2),
            "max_swap_percent": round(max_swap, 2),
            "min_swap_percent": round(min_swap, 2),
            "swap_total_gb": round(swap_total_gb, 2),
            "swap_used_gb": round(swap_used_gb, 2),
            "duration_seconds": (end_time - start_time).total_seconds(),
        }

        return AnomalyEvent(
            id=str(uuid.uuid4()),
            timestamp=start_time,
            end_time=end_time,
            severity=severity,
            type="swap_sustained_high_usage",
            confidence=confidence,
            metrics=event_metrics,
            baseline=None,
            top_processes=[],
            algorithm="swap_sustained_usage",
        )

    def _create_spike_event(
        self, metric: MemoryMetric, baseline_mean: float, spike_threshold: float
    ) -> AnomalyEvent:
        """
        Create an anomaly event for a swap spike.

        Args:
            metric: Metric with spike
            baseline_mean: Baseline swap usage
            spike_threshold: Threshold for spike detection

        Returns:
            AnomalyEvent object
        """
        # Calculate severity based on spike magnitude
        spike_magnitude = metric.swap_used_percent - baseline_mean
        if spike_magnitude > 50:
            severity = "critical"
        elif spike_magnitude > 30:
            severity = "warning"
        else:
            severity = "warning"

        # Calculate confidence based on deviation from baseline
        deviation_ratio = spike_magnitude / (baseline_mean + 1e-6)
        confidence = min(1.0, 0.5 + (deviation_ratio / 10.0))

        # Get swap statistics
        swap_total_gb = metric.swap_total / (1024 ** 3)
        swap_used_gb = metric.swap_used / (1024 ** 3)

        event_metrics = {
            "swap_percent": round(metric.swap_used_percent, 2),
            "baseline_mean": round(baseline_mean, 2),
            "spike_threshold": round(spike_threshold, 2),
            "spike_magnitude": round(spike_magnitude, 2),
            "swap_total_gb": round(swap_total_gb, 2),
            "swap_used_gb": round(swap_used_gb, 2),
        }

        return AnomalyEvent(
            id=str(uuid.uuid4()),
            timestamp=metric.timestamp,
            end_time=metric.timestamp,
            severity=severity,
            type="swap_spike",
            confidence=confidence,
            metrics=event_metrics,
            baseline=baseline_mean,
            top_processes=[],
            algorithm="swap_spike_detection",
        )

    def _calculate_severity(self, swap_percent: float) -> str:
        """
        Calculate severity based on swap usage percentage.

        Args:
            swap_percent: Swap usage percentage

        Returns:
            Severity level: "emergency", "critical", or "warning"
        """
        if swap_percent > 50:
            return "critical"
        elif swap_percent > 30:
            return "warning"
        else:
            return "warning"

    def get_name(self) -> str:
        """Get the detector name."""
        return "swap_anomaly"
