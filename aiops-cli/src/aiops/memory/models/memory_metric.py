"""
System-level memory metric data model
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryMetric:
    """System-level memory metric from /proc/meminfo and /proc/vmstat"""

    timestamp: datetime

    # Basic memory (from /proc/meminfo)
    mem_total: int          # Total physical memory (bytes)
    mem_free: int           # Free memory (bytes)
    mem_available: int      # Available memory (bytes)
    mem_used: int           # Used memory (calculated)

    # Cache and buffers
    buffers: int            # Buffer cache (bytes)
    cached: int             # Page cache (bytes)
    slab: int               # Slab cache (bytes)

    # Swap
    swap_total: int         # Total swap space (bytes)
    swap_free: int          # Free swap space (bytes)
    swap_used: int          # Used swap (calculated)
    swap_cached: int        # Cached swap (bytes)

    # Memory statistics (from /proc/vmstat)
    pswpin: int = 0         # Pages swapped in
    pswpout: int = 0        # Pages swapped out
    pgfault: int = 0        # Page faults
    pgmajfault: int = 0     # Major page faults

    # Dirty pages
    dirty: int = 0          # Dirty pages (bytes)
    writeback: int = 0      # Pages being written back (bytes)

    def __post_init__(self):
        """Validate memory metrics"""
        if self.mem_total <= 0:
            raise ValueError(f"mem_total must be positive, got {self.mem_total}")

        if not 0 <= self.mem_free <= self.mem_total:
            raise ValueError(f"mem_free must be between 0 and {self.mem_total}, got {self.mem_free}")

        if not 0 <= self.mem_available <= self.mem_total:
            raise ValueError(f"mem_available must be between 0 and {self.mem_total}, got {self.mem_available}")

        if self.swap_total < 0:
            raise ValueError(f"swap_total must be non-negative, got {self.swap_total}")

    @property
    def mem_used_percent(self) -> float:
        """Calculate memory usage percentage"""
        if self.mem_total == 0:
            return 0.0
        return round(100.0 * self.mem_used / self.mem_total, 2)

    @property
    def mem_available_percent(self) -> float:
        """Calculate available memory percentage"""
        if self.mem_total == 0:
            return 0.0
        return round(100.0 * self.mem_available / self.mem_total, 2)

    @property
    def swap_used_percent(self) -> float:
        """Calculate swap usage percentage"""
        if self.swap_total == 0:
            return 0.0
        return round(100.0 * self.swap_used / self.swap_total, 2)

    def to_dict(self):
        """Convert to dictionary for JSON/YAML output"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'mem_total_mb': self.mem_total // (1024 * 1024),
            'mem_free_mb': self.mem_free // (1024 * 1024),
            'mem_available_mb': self.mem_available // (1024 * 1024),
            'mem_used_mb': self.mem_used // (1024 * 1024),
            'mem_used_percent': self.mem_used_percent,
            'mem_available_percent': self.mem_available_percent,
            'swap_total_mb': self.swap_total // (1024 * 1024),
            'swap_used_mb': self.swap_used // (1024 * 1024),
            'swap_used_percent': self.swap_used_percent,
            'cached_mb': self.cached // (1024 * 1024),
            'buffers_mb': self.buffers // (1024 * 1024),
            'slab_mb': self.slab // (1024 * 1024),
            'dirty_mb': self.dirty // (1024 * 1024),
            'pswpin': self.pswpin,
            'pswpout': self.pswpout,
        }
