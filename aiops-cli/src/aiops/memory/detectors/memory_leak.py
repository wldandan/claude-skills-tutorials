"""Memory leak detector using linear regression analysis."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from aiops.core import BaseDetector
from aiops.cpu.models import AnomalyEvent
from aiops.memory.models import ProcessMemoryMetric


class MemoryLeakDetector(BaseDetector):
    """Detects memory leaks using linear regression on process memory usage over time."""

    def __init__(
        self,
        min_samples: int = 100,
        growth_threshold_mb: float = 50.0,
        confidence_threshold: float = 0.8,
    ):
        """
        Initialize the memory leak detector.

        Args:
            min_samples: Minimum number of samples required for analysis (default: 100)
            growth_threshold_mb: Memory growth threshold in MB/hour (default: 50.0)
            confidence_threshold: Minimum R² value for leak detection (default: 0.8)
        """
        self.min_samples = min_samples
        self.growth_threshold_mb = growth_threshold_mb
        self.confidence_threshold = confidence_threshold

    def detect(self, metrics: List[ProcessMemoryMetric]) -> List[AnomalyEvent]:
        """
        Detect memory leaks in process memory metrics.

        Algorithm:
        1. Group metrics by PID
        2. For each process, perform linear regression on RSS over time
        3. Calculate growth rate (MB/hour)
        4. Check if growth > threshold and R² > confidence_threshold
        5. Predict OOM time based on available memory

        Args:
            metrics: List of ProcessMemoryMetric objects

        Returns:
            List of AnomalyEvent objects for detected memory leaks
        """
        if not metrics or len(metrics) < self.min_samples:
            return []

        # Group metrics by PID
        process_metrics = self._group_by_pid(metrics)

        anomalies = []
        for pid, pid_metrics in process_metrics.items():
            if len(pid_metrics) < self.min_samples:
                continue

            # Analyze memory growth for this process
            leak_event = self._analyze_process_memory(pid, pid_metrics)
            if leak_event:
                anomalies.append(leak_event)

        return anomalies

    def _group_by_pid(
        self, metrics: List[ProcessMemoryMetric]
    ) -> Dict[int, List[ProcessMemoryMetric]]:
        """
        Group metrics by process ID.

        Args:
            metrics: List of ProcessMemoryMetric objects

        Returns:
            Dictionary mapping PID to list of metrics
        """
        grouped = {}
        for metric in metrics:
            if metric.pid not in grouped:
                grouped[metric.pid] = []
            grouped[metric.pid].append(metric)

        # Sort each group by timestamp
        for pid in grouped:
            grouped[pid].sort(key=lambda m: m.timestamp)

        return grouped

    def _analyze_process_memory(
        self, pid: int, metrics: List[ProcessMemoryMetric]
    ) -> Optional[AnomalyEvent]:
        """
        Analyze memory growth for a single process.

        Args:
            pid: Process ID
            metrics: List of metrics for this process

        Returns:
            AnomalyEvent if memory leak detected, None otherwise
        """
        # Extract timestamps and RSS values
        timestamps = np.array(
            [(m.timestamp - metrics[0].timestamp).total_seconds() for m in metrics]
        )
        rss_mb = np.array([m.rss_mb for m in metrics])

        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            timestamps, rss_mb
        )

        # Calculate R² (coefficient of determination)
        r_squared = r_value ** 2

        # Convert slope to MB/hour
        growth_rate_mb_hour = slope * 3600

        # Check if this is a memory leak
        if (
            growth_rate_mb_hour > self.growth_threshold_mb
            and r_squared > self.confidence_threshold
        ):
            # Predict OOM time (assuming system has limited memory)
            predicted_oom_time = self._predict_oom_time(
                metrics[-1], slope, intercept, timestamps[-1]
            )

            return self._create_anomaly_event(
                metrics[0].timestamp,
                metrics[-1].timestamp,
                metrics,
                growth_rate_mb_hour,
                r_squared,
                predicted_oom_time,
            )

        return None

    def _predict_oom_time(
        self,
        last_metric: ProcessMemoryMetric,
        slope: float,
        intercept: float,
        last_timestamp: float,
    ) -> Optional[datetime]:
        """
        Predict when the process might run out of memory.

        Args:
            last_metric: Last metric in the series
            slope: Regression slope (MB/second)
            intercept: Regression intercept
            last_timestamp: Last timestamp in seconds

        Returns:
            Predicted OOM datetime, or None if not predictable
        """
        # Assume a reasonable memory limit (e.g., 16GB for a process)
        # In production, this should be based on actual system limits
        memory_limit_mb = 16 * 1024

        current_rss = last_metric.rss_mb

        if slope <= 0:
            return None  # Memory not growing

        # Calculate time to reach limit
        time_to_limit_seconds = (memory_limit_mb - current_rss) / slope

        if time_to_limit_seconds < 0:
            return None  # Already over limit (shouldn't happen)

        predicted_time = last_metric.timestamp + timedelta(
            seconds=time_to_limit_seconds
        )

        return predicted_time

    def _create_anomaly_event(
        self,
        start_time: datetime,
        end_time: datetime,
        metrics: List[ProcessMemoryMetric],
        growth_rate_mb_hour: float,
        r_squared: float,
        predicted_oom_time: Optional[datetime],
    ) -> AnomalyEvent:
        """
        Create an anomaly event for a memory leak.

        Args:
            start_time: Analysis start time
            end_time: Analysis end time
            metrics: List of metrics
            growth_rate_mb_hour: Memory growth rate in MB/hour
            r_squared: R² value from regression
            predicted_oom_time: Predicted OOM time

        Returns:
            AnomalyEvent object
        """
        # Calculate severity based on growth rate and time to OOM
        severity = self._calculate_severity(growth_rate_mb_hour, predicted_oom_time)

        # Use R² as confidence
        confidence = min(1.0, r_squared)

        # Get process info from first metric
        process_name = metrics[0].name
        pid = metrics[0].pid

        # Calculate memory statistics
        initial_rss = metrics[0].rss_mb
        final_rss = metrics[-1].rss_mb
        total_growth = final_rss - initial_rss

        event_metrics = {
            "pid": pid,
            "process_name": process_name,
            "initial_rss_mb": round(initial_rss, 2),
            "final_rss_mb": round(final_rss, 2),
            "total_growth_mb": round(total_growth, 2),
            "growth_rate_mb_hour": round(growth_rate_mb_hour, 2),
            "r_squared": round(r_squared, 4),
        }

        if predicted_oom_time:
            time_to_oom_hours = (
                predicted_oom_time - end_time
            ).total_seconds() / 3600
            event_metrics["predicted_oom_time"] = predicted_oom_time.isoformat()
            event_metrics["time_to_oom_hours"] = round(time_to_oom_hours, 2)

        return AnomalyEvent(
            id=str(uuid.uuid4()),
            timestamp=start_time,
            end_time=end_time,
            severity=severity,
            type="memory_leak",
            confidence=confidence,
            metrics=event_metrics,
            baseline=None,
            top_processes=[],
            algorithm="memory_leak_linear_regression",
        )

    def _calculate_severity(
        self, growth_rate_mb_hour: float, predicted_oom_time: Optional[datetime]
    ) -> str:
        """
        Calculate severity based on growth rate and time to OOM.

        Args:
            growth_rate_mb_hour: Memory growth rate in MB/hour
            predicted_oom_time: Predicted OOM time

        Returns:
            Severity level: "emergency", "critical", or "warning"
        """
        # Check time to OOM first
        if predicted_oom_time:
            time_to_oom_hours = (
                predicted_oom_time - datetime.now()
            ).total_seconds() / 3600

            if time_to_oom_hours < 1:
                return "emergency"
            elif time_to_oom_hours < 6:
                return "critical"

        # Check growth rate
        if growth_rate_mb_hour > 200:
            return "critical"
        elif growth_rate_mb_hour > 100:
            return "warning"
        else:
            return "warning"

    def get_name(self) -> str:
        """Get the detector name."""
        return "memory_leak"
