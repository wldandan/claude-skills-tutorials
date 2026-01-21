"""
Process-level memory data collector
"""
import os
from datetime import datetime
from typing import List, Optional

import psutil

from aiops.memory.models import ProcessMemoryMetric
from aiops.core.base import BaseCollector
from aiops.core.exceptions import CollectionError


class ProcessMemoryCollector(BaseCollector):
    """Collects process-level memory metrics"""

    def __init__(self, max_processes: int = 50):
        """
        Initialize the process memory collector

        Args:
            max_processes: Maximum number of processes to collect
        """
        self.max_processes = max_processes
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the collector"""
        if not psutil.LINUX:
            raise CollectionError("Process memory collector is Linux-only")
        self._initialized = True

    def collect(self, pid: Optional[int] = None) -> List[ProcessMemoryMetric]:
        """
        Collect process memory metrics

        Args:
            pid: Optional process ID to collect. If None, collects top processes by memory.

        Returns:
            List of ProcessMemoryMetric

        Raises:
            CollectionError: If collection fails
        """
        if not self._initialized:
            self.initialize()

        try:
            if pid is not None:
                # Collect specific process
                return [self._collect_process(pid)]
            else:
                # Collect top processes by memory
                return self._collect_top_processes()

        except Exception as e:
            raise CollectionError(f"Failed to collect process memory metrics: {e}")

    def _collect_process(self, pid: int) -> ProcessMemoryMetric:
        """Collect memory metrics for a specific process"""
        try:
            proc = psutil.Process(pid)

            # Read /proc/<pid>/status for detailed memory info
            status_path = f"/proc/{pid}/status"
            mem_info = self._parse_proc_status(status_path)

            return ProcessMemoryMetric(
                timestamp=datetime.now(),
                pid=pid,
                name=proc.name(),
                vm_size=mem_info.get('VmSize', 0),
                vm_rss=mem_info.get('VmRSS', 0),
                vm_data=mem_info.get('VmData', 0),
                vm_stk=mem_info.get('VmStk', 0),
                vm_exe=mem_info.get('VmExe', 0),
                vm_lib=mem_info.get('VmLib', 0),
                vm_swap=mem_info.get('VmSwap', 0),
                username=proc.username(),
                status=proc.status(),
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            raise CollectionError(f"Failed to collect process {pid}: {e}")

    def _collect_top_processes(self) -> List[ProcessMemoryMetric]:
        """Collect top processes by memory usage"""
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
            try:
                pinfo = proc.info
                pid = pinfo['pid']

                # Read memory info from /proc/<pid>/status
                status_path = f"/proc/{pid}/status"
                if not os.path.exists(status_path):
                    continue

                mem_info = self._parse_proc_status(status_path)

                metric = ProcessMemoryMetric(
                    timestamp=datetime.now(),
                    pid=pid,
                    name=pinfo['name'],
                    vm_size=mem_info.get('VmSize', 0),
                    vm_rss=mem_info.get('VmRSS', 0),
                    vm_data=mem_info.get('VmData', 0),
                    vm_stk=mem_info.get('VmStk', 0),
                    vm_exe=mem_info.get('VmExe', 0),
                    vm_lib=mem_info.get('VmLib', 0),
                    vm_swap=mem_info.get('VmSwap', 0),
                    username=pinfo['username'] or 'unknown',
                    status=pinfo['status'] or 'R',
                )
                processes.append(metric)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort by RSS and return top N
        processes.sort(key=lambda p: p.vm_rss, reverse=True)
        return processes[:self.max_processes]

    def _parse_proc_status(self, status_path: str) -> dict:
        """Parse /proc/<pid>/status file for memory information"""
        mem_info = {}

        try:
            with open(status_path, 'r') as f:
                for line in f:
                    if line.startswith('Vm'):
                        parts = line.split()
                        if len(parts) >= 2:
                            key = parts[0].rstrip(':')
                            value = int(parts[1]) * 1024  # Convert KB to bytes
                            mem_info[key] = value
        except (IOError, ValueError):
            pass

        return mem_info

    def cleanup(self) -> None:
        """Clean up resources"""
        self._initialized = False
