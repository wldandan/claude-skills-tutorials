"""Disk statistics collector from /proc/diskstats."""

import os
from datetime import datetime
from typing import List, Optional

from aiops.core import BaseCollector
from aiops.diskio.models import DiskIOMetric
from aiops.core.exceptions import CollectionError


class DiskStatsCollector(BaseCollector):
    """Collects disk I/O statistics from /proc/diskstats."""

    PROC_DISKSTATS_PATH = "/proc/diskstats"

    def __init__(self, devices: Optional[List[str]] = None):
        """
        Initialize the disk stats collector.

        Args:
            devices: List of device names to monitor (e.g., ['sda', 'nvme0n1']).
                    If None, monitors all devices.
        """
        self.devices = devices
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the collector."""
        if not os.path.exists(self.PROC_DISKSTATS_PATH):
            raise CollectionError(
                f"Cannot read {self.PROC_DISKSTATS_PATH}. Are you on Linux?"
            )
        self._initialized = True

    def collect(self, device: Optional[str] = None) -> List[DiskIOMetric]:
        """
        Collect disk I/O metrics.

        Args:
            device: Specific device to collect (overrides self.devices)

        Returns:
            List of DiskIOMetric objects
        """
        if not self._initialized:
            raise CollectionError("Collector not initialized")

        try:
            metrics = []
            timestamp = datetime.now()

            with open(self.PROC_DISKSTATS_PATH, 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) < 14:
                        continue

                    # Parse device name (3rd field)
                    dev_name = parts[2]

                    # Skip partitions and loop devices by default
                    if self._should_skip_device(dev_name):
                        continue

                    # Check if we should monitor this device
                    if device:
                        if dev_name != device:
                            continue
                    elif self.devices and dev_name not in self.devices:
                        continue

                    # Parse statistics
                    metric = self._parse_diskstats_line(timestamp, parts)
                    if metric:
                        metrics.append(metric)

            return metrics

        except FileNotFoundError:
            raise CollectionError(
                f"Failed to read {self.PROC_DISKSTATS_PATH}: file not found"
            )
        except IOError as e:
            raise CollectionError(
                f"Failed to read {self.PROC_DISKSTATS_PATH}: {str(e)}"
            )
        except Exception as e:
            raise CollectionError(
                f"Failed to parse {self.PROC_DISKSTATS_PATH}: {str(e)}"
            )

    def _should_skip_device(self, device: str) -> bool:
        """
        Determine if a device should be skipped.

        Args:
            device: Device name

        Returns:
            True if device should be skipped
        """
        # Skip loop devices
        if device.startswith('loop'):
            return True

        # Skip ram devices
        if device.startswith('ram'):
            return True

        # Skip partitions (simple heuristic: ends with digit)
        # This will skip sda1, nvme0n1p1 but keep sda, nvme0n1
        if device[-1].isdigit() and not device.startswith('nvme'):
            return True

        # For NVMe, skip partitions (e.g., nvme0n1p1)
        if 'p' in device and device.startswith('nvme'):
            parts = device.split('p')
            if len(parts) == 2 and parts[1].isdigit():
                return True

        return False

    def _parse_diskstats_line(
        self, timestamp: datetime, parts: List[str]
    ) -> Optional[DiskIOMetric]:
        """
        Parse a line from /proc/diskstats.

        Format (11 or more fields after device name):
        reads_completed, reads_merged, sectors_read, time_reading_ms,
        writes_completed, writes_merged, sectors_written, time_writing_ms,
        io_in_progress, time_io_ms, weighted_time_io_ms,
        [discards_completed, discards_merged, sectors_discarded, time_discarding_ms],
        [flush_requests_completed, time_flushing_ms]

        Args:
            timestamp: Timestamp for the metric
            parts: Split line from diskstats

        Returns:
            DiskIOMetric or None if parsing fails
        """
        try:
            device = parts[2]

            # Basic I/O statistics (fields 3-13)
            reads_completed = int(parts[3])
            reads_merged = int(parts[4])
            sectors_read = int(parts[5])
            time_reading_ms = int(parts[6])
            writes_completed = int(parts[7])
            writes_merged = int(parts[8])
            sectors_written = int(parts[9])
            time_writing_ms = int(parts[10])
            io_in_progress = int(parts[11])
            time_io_ms = int(parts[12])
            weighted_time_io_ms = int(parts[13])

            # Optional discard statistics (fields 14-17)
            discards_completed = 0
            discards_merged = 0
            sectors_discarded = 0
            time_discarding_ms = 0
            if len(parts) >= 18:
                discards_completed = int(parts[14])
                discards_merged = int(parts[15])
                sectors_discarded = int(parts[16])
                time_discarding_ms = int(parts[17])

            # Optional flush statistics (fields 18-19)
            flush_requests_completed = 0
            time_flushing_ms = 0
            if len(parts) >= 20:
                flush_requests_completed = int(parts[18])
                time_flushing_ms = int(parts[19])

            return DiskIOMetric(
                timestamp=timestamp,
                device=device,
                reads_completed=reads_completed,
                reads_merged=reads_merged,
                sectors_read=sectors_read,
                time_reading_ms=time_reading_ms,
                writes_completed=writes_completed,
                writes_merged=writes_merged,
                sectors_written=sectors_written,
                time_writing_ms=time_writing_ms,
                io_in_progress=io_in_progress,
                time_io_ms=time_io_ms,
                weighted_time_io_ms=weighted_time_io_ms,
                discards_completed=discards_completed,
                discards_merged=discards_merged,
                sectors_discarded=sectors_discarded,
                time_discarding_ms=time_discarding_ms,
                flush_requests_completed=flush_requests_completed,
                time_flushing_ms=time_flushing_ms,
            )

        except (ValueError, IndexError) as e:
            # Skip malformed lines
            return None

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
