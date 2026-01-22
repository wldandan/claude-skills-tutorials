"""Process status collector from psutil."""

import psutil
from datetime import datetime
from typing import List, Optional

from aiops.core import BaseCollector
from aiops.process.models import ProcessStatusMetric
from aiops.core.exceptions import CollectionError


class ProcessStatusCollector(BaseCollector):
    """Collects process status information using psutil."""

    def __init__(self, pids: Optional[List[int]] = None, include_all: bool = False):
        """
        Initialize the process status collector.

        Args:
            pids: List of specific PIDs to monitor. If None, monitors all processes.
            include_all: Include all processes (default: False, only running processes)
        """
        self.pids = pids
        self.include_all = include_all
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the collector."""
        # Verify psutil is available
        try:
            psutil.process_iter()
        except Exception as e:
            raise CollectionError(f"Failed to initialize process collector: {str(e)}")

        self._initialized = True

    def collect(self, pid: Optional[int] = None) -> List[ProcessStatusMetric]:
        """
        Collect process status metrics.

        Args:
            pid: Specific process ID to collect (overrides self.pids)

        Returns:
            List of ProcessStatusMetric objects
        """
        if not self._initialized:
            raise CollectionError("Collector not initialized")

        try:
            metrics = []
            timestamp = datetime.now()

            if pid:
                # Collect specific process
                metric = self._collect_process(pid, timestamp)
                if metric:
                    metrics.append(metric)
            elif self.pids:
                # Collect specified PIDs
                for p in self.pids:
                    metric = self._collect_process(p, timestamp)
                    if metric:
                        metrics.append(metric)
            else:
                # Collect all processes
                for proc in psutil.process_iter(['pid']):
                    try:
                        metric = self._collect_process(proc.info['pid'], timestamp)
                        if metric:
                            metrics.append(metric)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            return metrics

        except Exception as e:
            raise CollectionError(f"Failed to collect process metrics: {str(e)}")

    def _collect_process(self, pid: int, timestamp: datetime) -> Optional[ProcessStatusMetric]:
        """
        Collect metrics for a specific process.

        Args:
            pid: Process ID
            timestamp: Timestamp for the metric

        Returns:
            ProcessStatusMetric or None if collection fails
        """
        try:
            proc = psutil.Process(pid)

            # Get basic info
            name = proc.name()
            status = proc.status()

            # Skip if not including all and process is zombie/dead
            if not self.include_all and status in ['Z', 'X']:
                return None

            # Get resource usage
            cpu_percent = proc.cpu_percent(interval=0)
            memory_info = proc.memory_info()
            memory_percent = proc.memory_percent()

            # Get process info
            ppid = proc.ppid()
            username = proc.username()
            create_time = proc.create_time()
            num_threads = proc.num_threads()

            # Get file descriptors (may fail on some systems)
            try:
                num_fds = proc.num_fds()
            except (AttributeError, psutil.AccessDenied):
                num_fds = 0

            # Get optional info
            try:
                cmdline = proc.cmdline()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                cmdline = None

            try:
                cwd = proc.cwd()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                cwd = None

            try:
                exe = proc.exe()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                exe = None

            return ProcessStatusMetric(
                timestamp=timestamp,
                pid=pid,
                name=name,
                status=status,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_rss=memory_info.rss,
                memory_vms=memory_info.vms,
                ppid=ppid,
                username=username,
                create_time=create_time,
                num_threads=num_threads,
                num_fds=num_fds,
                cmdline=cmdline,
                cwd=cwd,
                exe=exe,
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
        except Exception:
            return None

    def get_zombie_processes(self) -> List[ProcessStatusMetric]:
        """
        Get all zombie processes.

        Returns:
            List of ProcessStatusMetric objects for zombie processes
        """
        if not self._initialized:
            raise CollectionError("Collector not initialized")

        metrics = []
        timestamp = datetime.now()

        for proc in psutil.process_iter(['pid', 'status']):
            try:
                if proc.info['status'] == 'Z':
                    metric = self._collect_process(proc.info['pid'], timestamp)
                    if metric:
                        metrics.append(metric)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return metrics

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
