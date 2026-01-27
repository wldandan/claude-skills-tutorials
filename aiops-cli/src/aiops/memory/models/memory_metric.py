"""System memory metric model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class MemoryMetric:
    """System-level memory metrics from /proc/meminfo and /proc/vmstat."""

    timestamp: datetime

    # Memory totals (KB)
    mem_total: int
    mem_free: int
    mem_available: int
    buffers: int
    cached: int
    slab: int

    # Swap (KB)
    swap_total: int
    swap_free: int
    swap_cached: int

    # Memory stats
    dirty: int
    writeback: int
    active: int
    inactive: int

    # VM stats
    pswpin: int = 0
    pswpout: int = 0
    pgfault: int = 0
    pgmajfault: int = 0

    def __post_init__(self):
        """Validate memory metric."""
        if self.mem_total <= 0:
            raise ValueError("mem_total must be positive")

        if self.mem_free < 0:
            raise ValueError("mem_free cannot be negative")

        if self.mem_available < 0:
            raise ValueError("mem_available cannot be negative")

        if self.swap_total < 0:
            raise ValueError("swap_total cannot be negative")

    @property
    def mem_used(self) -> int:
        """Calculate used memory (KB)."""
        return self.mem_total - self.mem_free - self.buffers - self.cached

    @property
    def mem_used_percent(self) -> float:
        """Calculate memory usage percentage."""
        if self.mem_total == 0:
            return 0.0
        return (self.mem_used / self.mem_total) * 100

    @property
    def mem_available_percent(self) -> float:
        """Calculate available memory percentage."""
        if self.mem_total == 0:
            return 0.0
        return (self.mem_available / self.mem_total) * 100

    @property
    def swap_used(self) -> int:
        """Calculate used swap (KB)."""
        return self.swap_total - self.swap_free

    @property
    def swap_used_percent(self) -> float:
        """Calculate swap usage percentage."""
        if self.swap_total == 0:
            return 0.0
        return (self.swap_used / self.swap_total) * 100

    @property
    def mem_used_mb(self) -> float:
        """Memory used in MB."""
        return self.mem_used / 1024

    @property
    def mem_available_mb(self) -> float:
        """Memory available in MB."""
        return self.mem_available / 1024

    @property
    def swap_used_mb(self) -> float:
        """Swap used in MB."""
        return self.swap_used / 1024

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'mem_total': self.mem_total,
            'mem_free': self.mem_free,
            'mem_available': self.mem_available,
            'mem_used': self.mem_used,
            'mem_used_percent': self.mem_used_percent,
            'mem_available_percent': self.mem_available_percent,
            'buffers': self.buffers,
            'cached': self.cached,
            'slab': self.slab,
            'swap_total': self.swap_total,
            'swap_free': self.swap_free,
            'swap_used': self.swap_used,
            'swap_used_percent': self.swap_used_percent,
            'swap_cached': self.swap_cached,
            'dirty': self.dirty,
            'writeback': self.writeback,
            'active': self.active,
            'inactive': self.inactive,
            'pswpin': self.pswpin,
            'pswpout': self.pswpout,
            'pgfault': self.pgfault,
            'pgmajfault': self.pgmajfault,
        }
