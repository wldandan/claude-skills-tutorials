"""Dynamic baseline anomaly detector."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from scipy import stats

from aiops.cpu.detectors.base_detector import BaseDetector
from aiops.cpu.models import AnomalyEvent, Baseline, CPUMetric


class DynamicBaselineDetector(BaseDetector):
    """Detects CPU anomalies using dynamic baseline calculation."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the dynamic baseline detector.

        Args:
            config: Configuration dictionary with keys:
                - window_days: Days of historical data for baseline (default: 7)
                - std_multiplier: Standard deviation multiplier (default: 2.0)
        """
        self.window_days = config.get("window_days", 7)
        self.std_multiplier = config.get("std_multiplier", 2.0)
        self._baseline: Optional[Baseline] = None

    def detect(self, metrics: List[CPUMetric]) -> List[AnomalyEvent]:
        """
        Detect CPU anomalies using dynamic baseline.

        Args:
            metrics: List of CPUMetric objects to analyze

        Returns:
            List of AnomalyEvent objects
        """
        if not metrics or len(metrics) < 10:
            return []

        # Calculate baseline from historical data (excluding last 10% as test data)
        split_idx = int(len(metrics) * 0.9)
        historical_metrics = metrics[:split_idx]
        test_metrics = metrics[split_idx:]

        if len(historical_metrics) < 10:
            return []

        # Calculate baseline
        self._baseline = self._calculate_baseline(historical_metrics)

        # Detect anomalies in test data
        anomalies = []
        for metric in test_metrics:
            if self._is_anomaly(metric):
                anomaly = self._create_anomaly_event(metric, test_metrics)
                if anomaly:
                    anomalies.append(anomaly)

        return anomalies

    def _calculate_baseline(self, metrics: List[CPUMetric]) -> Baseline:
        """
        Calculate statistical baseline from metrics.

        Args:
            metrics: Historical metrics

        Returns:
            Baseline object
        """
        cpu_values = [m.cpu_percent for m in metrics]

        return Baseline(
            metric_name="cpu_percent",
            window_days=self.window_days,
            mean=float(np.mean(cpu_values)),
            std=float(np.std(cpu_values)),
            min=float(np.min(cpu_values)),
            max=float(np.max(cpu_values)),
            percentile_95=float(np.percentile(cpu_values, 95)),
            updated_at=datetime.now(),
        )

    def _is_anomaly(self, metric: CPUMetric) -> bool:
        """
        Check if a metric is an anomaly.

        Args:
            metric: Metric to check

        Returns:
            True if anomaly, False otherwise
        """
        if self._baseline is None:
            return False

        threshold = self._baseline.get_threshold(self.std_multiplier)
        return metric.cpu_percent > threshold

    def _create_anomaly_event(
        self,
        metric: CPUMetric,
        context_metrics: List[CPUMetric],
    ) -> Optional[AnomalyEvent]:
        """
        Create an anomaly event.

        Args:
            metric: The anomalous metric
            context_metrics: Context metrics for analysis

        Returns:
            AnomalyEvent object or None
        """
        if self._baseline is None:
            return None

        threshold = self._baseline.get_threshold(self.std_multiplier)
        deviation = metric.cpu_percent - self._baseline.mean
        z_score = deviation / self._baseline.std if self._baseline.std > 0 else 0

        # Determine severity based on z-score
        if z_score > 4:
            severity = "emergency"
        elif z_score > 3:
            severity = "critical"
        else:
            severity = "warning"

        # Calculate confidence based on z-score
        confidence = min(1.0, 0.5 + (z_score / 10.0))

        return AnomalyEvent(
            id=str(uuid.uuid4()),
            timestamp=metric.timestamp,
            end_time=metric.timestamp,
            severity=severity,
            type="high_cpu",
            confidence=confidence,
            metrics={
                "avg_cpu_percent": metric.cpu_percent,
                "baseline_cpu_percent": round(self._baseline.mean, 2),
                "threshold_percent": round(threshold, 2),
                "z_score": round(z_score, 2),
            },
            baseline=self._baseline.mean,
            top_processes=[],
            algorithm="dynamic_baseline",
        )

    def get_name(self) -> str:
        """Get the detector name."""
        return "dynamic_baseline"

    def get_baseline(self) -> Optional[Baseline]:
        """Get the current baseline."""
        return self._baseline
