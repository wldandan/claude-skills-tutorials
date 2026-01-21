"""
System-level memory data collector
"""
import os
from datetime import datetime
from typing import List

from aiops.memory.models import MemoryMetric
from aiops.core.base import BaseCollector
from aiops.core.exceptions import CollectionError


class SystemMemoryCollector(BaseCollector):
    """Collects system-level memory metrics from /proc/meminfo and /proc/vmstat"""

    PROC_MEMINFO_PATH = "/proc/meminfo"
    PROC_VMSTAT_PATH = "/proc/vmstat"

    def __init__(self):
        """Initialize the system memory collector"""
        self._initialized = False
        self._prev_pswpin = 0
        self._prev_pswpout = 0

    def initialize(self) -> None:
        """Initialize the collector"""
        if not os.path.exists(self.PROC_MEMINFO_PATH):
            raise CollectionError(
                f"Cannot read {self.PROC_MEMINFO_PATH}. Are you on Linux?"
            )
        if not os.path.exists(self.PROC_VMSTAT_PATH):
            raise CollectionError(
                f"Cannot read {self.PROC_VMSTAT_PATH}. Are you on Linux?"
            )
        self._initialized = True

    def collect(self) -> List[MemoryMetric]:
        """
        Collect system memory metrics

        Returns:
            List containing a single MemoryMetric

        Raises:
            CollectionError: If collection fails
        """
        if not self._initialized:
            self.initialize()

        try:
            # Parse /proc/meminfo
            meminfo = self._parse_meminfo()

            # Parse /proc/vmstat
            vmstat = self._parse_vmstat()

            # Calculate derived values
            mem_used = meminfo['MemTotal'] - meminfo['MemFree'] - meminfo['Buffers'] - meminfo['Cached']
            swap_used = meminfo['SwapTotal'] - meminfo['SwapFree']

            metric = MemoryMetric(
                timestamp=datetime.now(),
                mem_total=meminfo['MemTotal'],
                mem_free=meminfo['MemFree'],
                mem_available=meminfo.get('MemAvailable', meminfo['MemFree']),
                mem_used=mem_used,
                buffers=meminfo['Buffers'],
                cached=meminfo['Cached'],
                slab=meminfo.get('Slab', 0),
                swap_total=meminfo['SwapTotal'],
                swap_free=meminfo['SwapFree'],
                swap_used=swap_used,
                swap_cached=meminfo.get('SwapCached', 0),
                pswpin=vmstat.get('pswpin', 0),
                pswpout=vmstat.get('pswpout', 0),
                pgfault=vmstat.get('pgfault', 0),
                pgmajfault=vmstat.get('pgmajfault', 0),
                dirty=meminfo.get('Dirty', 0),
                writeback=meminfo.get('Writeback', 0),
            )

            return [metric]

        except Exception as e:
            raise CollectionError(f"Failed to collect memory metrics: {e}")

    def _parse_meminfo(self) -> dict:
        """Parse /proc/meminfo file"""
        meminfo = {}

        with open(self.PROC_MEMINFO_PATH, 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(':')
                    value = int(parts[1]) * 1024  # Convert KB to bytes
                    meminfo[key] = value

        return meminfo

    def _parse_vmstat(self) -> dict:
        """Parse /proc/vmstat file"""
        vmstat = {}

        with open(self.PROC_VMSTAT_PATH, 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) == 2:
                    key = parts[0]
                    value = int(parts[1])
                    vmstat[key] = value

        return vmstat

    def cleanup(self) -> None:
        """Clean up resources"""
        self._initialized = False
        self._prev_pswpin = 0
        self._prev_pswpout = 0
