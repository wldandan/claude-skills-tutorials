"""Process-level CPU data collector."""

from datetime import datetime
from typing import List

import psutil

from aiops.cpu.models import ProcessMetric
from aiops.core import BaseCollector, CollectionError


class ProcessCPUCollector(BaseCollector):
    """Collects process-level CPU metrics."""

    def __init__(self, max_processes: int = 50):
        """
        Initialize the process CPU collector.

        Args:
            max_processes: Maximum number of processes to collect
        """
        self.max_processes = max_processes
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the collector."""
        if not psutil.LINUX:
            raise CollectionError("Process collector is Linux-only")
        self._initialized = True

    def collect(self, pid: int = None) -> List[ProcessMetric]:
        """
        Collect process CPU metrics.

        Args:
            pid: Optional process ID to collect. If None, collects top processes.

        Returns:
            List of ProcessMetric for the specified process or top processes

        Raises:
            CollectionError: If collection fails
        """
        if not self._initialized:
            self.initialize()

        try:
            # If specific PID requested
            if pid is not None:
                try:
                    proc = psutil.Process(pid)
                    pinfo = {
                        "pid": proc.pid,
                        "name": proc.name(),
                        "cpu_percent": proc.cpu_percent(),
                        "memory_percent": proc.memory_percent(),
                        "username": proc.username(),
                        "status": proc.status(),
                        "num_threads": proc.num_threads(),
                        "cpu_times": proc.cpu_times(),
                    }
                    metric = ProcessMetric(
                        timestamp=datetime.now(),
                        pid=pinfo["pid"],
                        name=pinfo["name"],
                        cpu_percent=pinfo["cpu_percent"] if pinfo["cpu_percent"] else 0.0,
                        user_time=pinfo["cpu_times"].user if pinfo["cpu_times"] else 0.0,
                        system_time=pinfo["cpu_times"].system if pinfo["cpu_times"] else 0.0,
                        num_threads=pinfo["num_threads"] or 0,
                        status=pinfo["status"] or "R",
                        memory_percent=pinfo["memory_percent"] or 0.0,
                        username=pinfo["username"] or "unknown",
                    )
                    return [metric]
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    raise CollectionError(f"Failed to collect process {pid}: {e}")

            # Get all processes sorted by CPU usage
            processes = []

            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "username", "status", "num_threads", "cpu_times"]):
                try:
                    pinfo = proc.info
                    if pinfo["cpu_percent"] is None:
                        continue

                    metric = ProcessMetric(
                        timestamp=datetime.now(),
                        pid=pinfo["pid"],
                        name=pinfo["name"],
                        cpu_percent=pinfo["cpu_percent"],
                        user_time=pinfo["cpu_times"].user if pinfo["cpu_times"] else 0.0,
                        system_time=pinfo["cpu_times"].system if pinfo["cpu_times"] else 0.0,
                        num_threads=pinfo["num_threads"] or 0,
                        status=pinfo["status"] or "R",
                        memory_percent=pinfo["memory_percent"] or 0.0,
                        username=pinfo["username"] or "unknown",
                    )
                    processes.append(metric)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process ended or access denied, skip
                    continue

            # Sort by CPU usage and return top N
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)
            return processes[: self.max_processes]

        except psutil.Error as e:
            raise CollectionError(f"Failed to collect process metrics: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False
