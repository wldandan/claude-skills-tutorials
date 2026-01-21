"""OOM risk detector for predicting out-of-memory conditions."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import numpy as np
from scipy import stats

from aiops.core import BaseDetector
from aiops.cpu.models import AnomalyEvent
from aiops.memory.models import MemoryMetric


class OOMRiskDetector(BaseDetector):
    """Detects OOM (Out-Of-Memory) risk by analyzing system memory trends."""

    def __init__(
        self,
        prediction_window_hours: int = 24,
        risk_threshold_percent: float = 90.0,
        min_samples: int = 30,
    ):
        """
        Initialize the OOM risk detector.

        Args:
            prediction_window_hours: Time window for OOM prediction (default: 24)
            risk_threshold_percent: Memory usage threshold for risk (default: 90.0)
            min_samples: Minimum number of samples required (default: 30)
        """
        self.prediction_window_hours = prediction_window_hours
        self.risk_threshold_percent = risk_threshold_percent
        self.min_samples = min_samples

    def detect(self, metrics: List[MemoryMetric]) -> List[AnomalyEvent]:
        """
        Detect OOM risk in system memory metrics.

        Algorithm:
        1. Calculate current memory usage trend using linear regression
        2. Predict future memory usage within prediction window
        3. Compare predicted usage with available memory
        4. Calculate time to OOM if trend continues
        5. Generate alert if OOM predicted within window

        Args:
            metrics: List of MemoryMetric objects

        Returns:
            List of AnomalyEvent objects for detected OOM risks
        """
        if not metrics or len(metrics) < self.min_samples:
            return []

        # Sort metrics by timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)

        # Analyze memory trend
        oom_event = self._analyze_memory_trend(sorted_metrics)

        if oom_event:
            return [oom_event]
        else:
            return []

    def _analyze_memory_trend(
        self, metrics: List[MemoryMetric]
    ) -> Optional[AnomalyEvent]:
        """
        Analyze memory usage trend and predict OOM risk.

        Args:
            metrics: Sorted list of MemoryMetric objects

        Returns:
            AnomalyEvent if OOM risk detected, None otherwise
        """
        # Extract timestamps and memory usage percentages
        timestamps = np.array(
            [(m.timestamp - metrics[0].timestamp).total_seconds() for m in metrics]
        )
        mem_used_percent = np.array([m.mem_used_percent for m in metrics])

        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            timestamps, mem_used_percent
        )

        # Calculate R²
        r_squared = r_value ** 2

        # Only proceed if we have a reasonable trend (R² > 0.5)
        if r_squared < 0.5:
            return None

        # Current memory usage
        current_usage = metrics[-1].mem_used_percent
        current_time = metrics[-1].timestamp

        # Predict memory usage at prediction window
        prediction_seconds = self.prediction_window_hours * 3600
        predicted_usage = slope * (timestamps[-1] + prediction_seconds) + intercept

        # Check if predicted usage exceeds threshold
        if predicted_usage >= self.risk_threshold_percent:
            # Calculate time to reach threshold
            if slope > 0:
                time_to_threshold_seconds = (
                    self.risk_threshold_percent - (slope * timestamps[-1] + intercept)
                ) / slope
                time_to_oom = current_time + timedelta(
                    seconds=time_to_threshold_seconds
                )
            else:
                time_to_oom = None

            # Only alert if OOM is within prediction window
            if time_to_oom and (time_to_oom - current_time).total_seconds() <= (
                self.prediction_window_hours * 3600
            ):
                return self._create_anomaly_event(
                    metrics[0].timestamp,
                    metrics[-1].timestamp,
                    metrics,
                    current_usage,
                    predicted_usage,
                    time_to_oom,
                    r_squared,
                )

        return None

    def _create_anomaly_event(
        self,
        start_time: datetime,
        end_time: datetime,
        metrics: List[MemoryMetric],
        current_usage: float,
        predicted_usage: float,
        time_to_oom: datetime,
        r_squared: float,
    ) -> AnomalyEvent:
        """
        Create an anomaly event for OOM risk.

        Args:
            start_time: Analysis start time
            end_time: Analysis end time
            metrics: List of metrics
            current_usage: Current memory usage percentage
            predicted_usage: Predicted memory usage percentage
            time_to_oom: Predicted time to OOM
            r_squared: R² value from regression

        Returns:
            AnomalyEvent object
        """
        # Calculate severity based on time to OOM
        time_to_oom_hours = (time_to_oom - end_time).total_seconds() / 3600
        severity = self._calculate_severity(time_to_oom_hours)

        # Use R² as confidence
        confidence = min(1.0, r_squared)

        # Calculate memory statistics
        avg_usage = sum(m.mem_used_percent for m in metrics) / len(metrics)
        max_usage = max(m.mem_used_percent for m in metrics)

        # Get current memory info
        last_metric = metrics[-1]
        total_memory_gb = last_metric.mem_total / (1024 ** 3)
        available_memory_gb = last_metric.mem_available / (1024 ** 3)

        event_metrics = {
            "current_usage_percent": round(current_usage, 2),
            "predicted_usage_percent": round(predicted_usage, 2),
            "avg_usage_percent": round(avg_usage, 2),
            "max_usage_percent": round(max_usage, 2),
            "total_memory_gb": round(total_memory_gb, 2),
            "available_memory_gb": round(available_memory_gb, 2),
            "time_to_oom_hours": round(time_to_oom_hours, 2),
            "predicted_oom_time": time_to_oom.isoformat(),
            "r_squared": round(r_squared, 4),
        }

        return AnomalyEvent(
            id=str(uuid.uuid4()),
            timestamp=start_time,
            end_time=end_time,
            severity=severity,
            type="oom_risk",
            confidence=confidence,
            metrics=event_metrics,
            baseline=None,
            top_processes=[],
            algorithm="oom_risk_prediction",
        )

    def _calculate_severity(self, time_to_oom_hours: float) -> str:
        """
        Calculate severity based on time to OOM.

        Args:
            time_to_oom_hours: Hours until predicted OOM

        Returns:
            Severity level: "emergency", "critical", or "warning"
        """
        if time_to_oom_hours < 1:
            return "emergency"
        elif time_to_oom_hours < 6:
            return "critical"
        elif time_to_oom_hours < 24:
            return "warning"
        else:
            return "warning"

    def get_name(self) -> str:
        """Get the detector name."""
        return "oom_risk"
