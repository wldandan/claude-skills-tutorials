"""Process I/O collector from /proc/<pid>/io."""

import os
import psutil
from datetime import datetime
from typing import List, Optional

from aiops.core import BaseCollector
from aiops.diskio.models import ProcessIOMetric
from aiops.core.exceptions import CollectionError


class ProcessIOCollector(BaseCollector):
    """Collects process I/O statistics from /proc/<pid>/io."""

    def __init__(self, max_processes: int = 10):
        """
        Initialize the process I/O collector.

        Args:
            max_processes: Maximum number of processes to collect (top by I/O)
        """
        self.max_processes = max_processes
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the collector."""
        if not psutil.LINUX:
            raise CollectionError("Process I/O collector is Linux-only")
        self._initialized = True

    def collect(self, pid: Optional[int] = None) -> List[ProcessIOMetric]:
        """
        Collect process I/O metrics.

        Args:
            pid: Specific process ID to collect. If None, collect top processes by I/O.

        Returns:
            List of ProcessIOMetric objects
        """
        if not self._initialized:
            raise CollectionError("Collector not initialized")

        if pid:
            # Collect specific process
            metrics = self._collect_process(pid)
            return metrics if metrics else []
        else:
            # Collect top N processes by I/O
            return self._collect_top_processes()

    def _collect_process(self, pid: int) -> Optional[ProcessIOMetric]:
        """
        Collect I/O metrics for a specific process.

        Args:
            pid: Process ID

        Returns:
            ProcessIOMetric or None if collection fails
        """
        try:
            timestamp = datetime.now()
            io_counters = self._read_proc_io(pid)

            if not io_counters:
                return None

            # Get process info
            try:
                proc = psutil.Process(pid)
                name = proc.name()
                username = proc.username()
                status = proc.status()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                name = f"pid_{pid}"
                username = ""
                status = ""

            return ProcessIOMetric(
                timestamp=timestamp,
                pid=pid,
                name=name,
                rchar=io_counters['rchar'],
                wchar=io_counters['wchar'],
                syscr=io_counters['syscr'],
                syscw=io_counters['syscw'],
                read_bytes=io_counters['read_bytes'],
                write_bytes=io_counters['write_bytes'],
                cancelled_write_bytes=io_counters['cancelled_write_bytes'],
                username=username,
                status=status,
            )

        except Exception:
            return None

    def _collect_top_processes(self) -> List[ProcessIOMetric]:
        """
        Collect I/O metrics for top N processes by I/O.

        Returns:
            List of ProcessIOMetric objects sorted by total I/O
        """
        metrics = []

        for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
            try:
                pid = proc.info['pid']
                metric = self._collect_process(pid)
                if metric:
                    metrics.append(metric)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by total I/O bytes (descending)
        metrics.sort(key=lambda m: m.total_io_bytes, reverse=True)

        # Return top N
        return metrics[:self.max_processes]

    def _read_proc_io(self, pid: int) -> Optional[dict]:
        """
        Read /proc/<pid>/io file.

        Format:
        rchar: <number>
        wchar: <number>
        syscr: <number>
        syscw: <number>
        read_bytes: <number>
        write_bytes: <number>
        cancelled_write_bytes: <number>

        Args:
            pid: Process ID

        Returns:
            Dictionary of I/O counters or None if read fails
        """
        io_path = f"/proc/{pid}/io"

        try:
            with open(io_path, 'r') as f:
                io_data = {}
                for line in f:
                    if ':' not in line:
                        continue
                    key, value = line.split(':', 1)
                    io_data[key.strip()] = int(value.strip())

                # Validate we have all required fields
                required_fields = [
                    'rchar', 'wchar', 'syscr', 'syscw',
                    'read_bytes', 'write_bytes', 'cancelled_write_bytes'
                ]
                if all(field in io_data for field in required_fields):
                    return io_data

                return None

        except (FileNotFoundError, PermissionError, ValueError):
            return None

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
