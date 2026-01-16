"""System-level CPU data collector."""

import os
from datetime import datetime
from typing import List

from aiops.cpu.models import CPUMetric
from aiops.core import BaseCollector, CollectionError, calculate_cpu_percent


class SystemCPUCollector(BaseCollector):
    """Collects system-level CPU metrics from /proc/stat."""

    PROC_STAT_PATH = "/proc/stat"

    def __init__(self):
        """Initialize the system CPU collector."""
        self._prev_total = 0.0
        self._prev_idle = 0.0
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the collector."""
        if not os.path.exists(self.PROC_STAT_PATH):
            raise CollectionError(
                f"Cannot read {self.PROC_STAT_PATH}. Are you on Linux?"
            )
        self._initialized = True

    def collect(self) -> List[CPUMetric]:
        """
        Collect system CPU metrics.

        Returns:
            List containing a single CPUMetric

        Raises:
            CollectionError: If collection fails
        """
        if not self._initialized:
            self.initialize()

        try:
            with open(self.PROC_STAT_PATH, "r") as f:
                lines = f.readlines()
        except IOError as e:
            raise CollectionError(f"Failed to read {self.PROC_STAT_PATH}: {e}")

        metrics = []

        for line in lines:
            if not line.startswith("cpu"):
                break

            parts = line.split()
            cpu_name = parts[0]

            # Parse CPU time values from /proc/stat
            # Format: cpu user nice system idle iowait irq softirq steal guest guest_nice
            if len(parts) < 5:
                continue

            try:
                user = int(parts[1])
                nice = int(parts[2])
                system = int(parts[3])
                idle = int(parts[4])
                iowait = int(parts[5]) if len(parts) > 5 else 0
                irq = int(parts[6]) if len(parts) > 6 else 0
                softirq = int(parts[7]) if len(parts) > 7 else 0
                steal = int(parts[8]) if len(parts) > 8 else 0

                total = user + nice + system + idle + iowait + irq + softirq + steal

                # Calculate CPU percentage
                cpu_percent = calculate_cpu_percent(total, idle, self._prev_total, self._prev_idle)

                # Calculate component percentages
                if total > 0 and total - self._prev_total > 0:
                    total_delta = total - self._prev_total
                    idle_delta = idle - self._prev_idle
                    active_delta = total_delta - idle_delta

                    cpu_user = round(100 * (user - (self._prev_total - idle - self._prev_idle)) / total_delta, 2)
                    cpu_system = round(100 * (system - 0) / total_delta, 2)
                    cpu_idle = round(100 * idle_delta / total_delta, 2)
                    cpu_iowait = round(100 * (iowait - 0) / total_delta, 2)
                    cpu_steal = round(100 * (steal - 0) / total_delta, 2)
                else:
                    # First sample or no change
                    cpu_user = 0.0
                    cpu_system = 0.0
                    cpu_idle = 100.0
                    cpu_iowait = 0.0
                    cpu_steal = 0.0

                # Store for next calculation
                self._prev_total = total
                self._prev_idle = idle

                if cpu_name == "cpu":
                    # Aggregate CPU
                    metric = CPUMetric(
                        timestamp=datetime.now(),
                        cpu_percent=cpu_percent,
                        cpu_user=cpu_user,
                        cpu_system=cpu_system,
                        cpu_idle=cpu_idle,
                        cpu_iowait=cpu_iowait,
                        cpu_steal=cpu_steal,
                    )
                    metrics.append(metric)
                elif cpu_name.startswith("cpu"):
                    # Per-core CPU - will be added later
                    pass

            except (ValueError, IndexError) as e:
                raise CollectionError(f"Failed to parse CPU data from {self.PROC_STAT_PATH}: {e}")

        return metrics

    def cleanup(self) -> None:
        """Clean up resources."""
        self._prev_total = 0.0
        self._prev_idle = 0.0
        self._initialized = False
