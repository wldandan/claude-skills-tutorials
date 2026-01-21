"""Disk I/O metric data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DiskIOMetric:
    """Disk I/O metrics from /proc/diskstats."""

    timestamp: datetime
    device: str  # Device name (e.g., 'sda', 'nvme0n1')

    # Read statistics
    reads_completed: int  # Number of reads completed
    reads_merged: int  # Number of reads merged
    sectors_read: int  # Number of sectors read
    time_reading_ms: int  # Time spent reading (ms)

    # Write statistics
    writes_completed: int  # Number of writes completed
    writes_merged: int  # Number of writes merged
    sectors_written: int  # Number of sectors written
    time_writing_ms: int  # Time spent writing (ms)

    # I/O statistics
    io_in_progress: int  # I/Os currently in progress
    time_io_ms: int  # Time spent doing I/Os (ms)
    weighted_time_io_ms: int  # Weighted time spent doing I/Os (ms)

    # Discard statistics (optional, for newer kernels)
    discards_completed: Optional[int] = 0
    discards_merged: Optional[int] = 0
    sectors_discarded: Optional[int] = 0
    time_discarding_ms: Optional[int] = 0

    # Flush statistics (optional, for newer kernels)
    flush_requests_completed: Optional[int] = 0
    time_flushing_ms: Optional[int] = 0

    def __post_init__(self):
        """Validate disk I/O metrics."""
        if not self.device:
            raise ValueError("device cannot be empty")

        # Validate non-negative values
        for field in [
            'reads_completed', 'reads_merged', 'sectors_read', 'time_reading_ms',
            'writes_completed', 'writes_merged', 'sectors_written', 'time_writing_ms',
            'io_in_progress', 'time_io_ms', 'weighted_time_io_ms'
        ]:
            value = getattr(self, field)
            if value < 0:
                raise ValueError(f"{field} must be non-negative, got {value}")

    @property
    def read_bytes(self) -> int:
        """Total bytes read (assuming 512-byte sectors)."""
        return self.sectors_read * 512

    @property
    def write_bytes(self) -> int:
        """Total bytes written (assuming 512-byte sectors)."""
        return self.sectors_written * 512

    @property
    def total_io_operations(self) -> int:
        """Total I/O operations (reads + writes)."""
        return self.reads_completed + self.writes_completed

    @property
    def avg_read_time_ms(self) -> float:
        """Average read time in milliseconds."""
        if self.reads_completed == 0:
            return 0.0
        return self.time_reading_ms / self.reads_completed

    @property
    def avg_write_time_ms(self) -> float:
        """Average write time in milliseconds."""
        if self.writes_completed == 0:
            return 0.0
        return self.time_writing_ms / self.writes_completed

    @property
    def utilization_percent(self) -> float:
        """I/O utilization percentage (time_io_ms / 1000 for 1 second interval)."""
        # This is approximate and should be calculated based on time delta
        # For now, return as-is for single snapshot
        return min(100.0, (self.time_io_ms / 10.0))

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'device': self.device,
            'reads_completed': self.reads_completed,
            'reads_merged': self.reads_merged,
            'sectors_read': self.sectors_read,
            'time_reading_ms': self.time_reading_ms,
            'writes_completed': self.writes_completed,
            'writes_merged': self.writes_merged,
            'sectors_written': self.sectors_written,
            'time_writing_ms': self.time_writing_ms,
            'io_in_progress': self.io_in_progress,
            'time_io_ms': self.time_io_ms,
            'weighted_time_io_ms': self.weighted_time_io_ms,
            'read_bytes': self.read_bytes,
            'write_bytes': self.write_bytes,
            'total_io_operations': self.total_io_operations,
            'avg_read_time_ms': self.avg_read_time_ms,
            'avg_write_time_ms': self.avg_write_time_ms,
        }
