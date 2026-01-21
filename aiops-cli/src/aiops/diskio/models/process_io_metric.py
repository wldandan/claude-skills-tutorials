"""Process I/O metric data model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProcessIOMetric:
    """Process I/O metrics from /proc/<pid>/io."""

    timestamp: datetime
    pid: int
    name: str

    # Character-level I/O
    rchar: int  # Characters read (including cache)
    wchar: int  # Characters written (including cache)

    # System call I/O
    syscr: int  # Read syscalls
    syscw: int  # Write syscalls

    # Actual I/O
    read_bytes: int  # Bytes actually read from storage
    write_bytes: int  # Bytes actually written to storage

    # Cancelled writes
    cancelled_write_bytes: int  # Bytes cancelled before writing

    # Additional metadata
    username: str = ""
    status: str = ""  # Process status (R, S, D, Z, T, etc.)

    def __post_init__(self):
        """Validate process I/O metrics."""
        if self.pid <= 0:
            raise ValueError(f"pid must be positive, got {self.pid}")

        # Validate non-negative values
        for field in ['rchar', 'wchar', 'syscr', 'syscw', 'read_bytes',
                      'write_bytes', 'cancelled_write_bytes']:
            value = getattr(self, field)
            if value < 0:
                raise ValueError(f"{field} must be non-negative, got {value}")

    @property
    def read_bytes_mb(self) -> float:
        """Read bytes in MB."""
        return self.read_bytes / (1024 * 1024)

    @property
    def write_bytes_mb(self) -> float:
        """Write bytes in MB."""
        return self.write_bytes / (1024 * 1024)

    @property
    def total_io_bytes(self) -> int:
        """Total I/O bytes (read + write)."""
        return self.read_bytes + self.write_bytes

    @property
    def total_io_mb(self) -> float:
        """Total I/O in MB."""
        return self.total_io_bytes / (1024 * 1024)

    @property
    def avg_read_syscall_bytes(self) -> float:
        """Average bytes per read syscall."""
        if self.syscr == 0:
            return 0.0
        return self.read_bytes / self.syscr

    @property
    def avg_write_syscall_bytes(self) -> float:
        """Average bytes per write syscall."""
        if self.syscw == 0:
            return 0.0
        return self.write_bytes / self.syscw

    @property
    def write_efficiency_percent(self) -> float:
        """Write efficiency (actual written / requested to write)."""
        if self.wchar == 0:
            return 100.0
        actual_written = self.write_bytes
        requested = self.wchar - self.cancelled_write_bytes
        if requested == 0:
            return 100.0
        return min(100.0, (actual_written / requested) * 100.0)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'pid': self.pid,
            'name': self.name,
            'rchar': self.rchar,
            'wchar': self.wchar,
            'syscr': self.syscr,
            'syscw': self.syscw,
            'read_bytes': self.read_bytes,
            'write_bytes': self.write_bytes,
            'cancelled_write_bytes': self.cancelled_write_bytes,
            'username': self.username,
            'status': self.status,
            'read_bytes_mb': self.read_bytes_mb,
            'write_bytes_mb': self.write_bytes_mb,
            'total_io_mb': self.total_io_mb,
        }
