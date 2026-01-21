"""
Process-level memory metric data model
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProcessMemoryMetric:
    """Process-level memory metric from /proc/<pid>/status and statm"""

    timestamp: datetime
    pid: int
    name: str

    # Memory sizes (from /proc/<pid>/status)
    vm_size: int        # Virtual memory size (bytes)
    vm_rss: int         # Resident set size (bytes)
    vm_data: int        # Data segment size (bytes)
    vm_stk: int         # Stack size (bytes)
    vm_exe: int         # Executable size (bytes)
    vm_lib: int         # Shared library size (bytes)
    vm_swap: int        # Swap usage (bytes)

    # Additional info
    username: str
    status: str         # Process status (R, S, D, Z, T, W, X, I)

    def __post_init__(self):
        """Validate process memory metrics"""
        if self.pid <= 0:
            raise ValueError(f"pid must be positive, got {self.pid}")

        if self.vm_size < 0:
            raise ValueError(f"vm_size must be non-negative, got {self.vm_size}")

        if self.vm_rss < 0:
            raise ValueError(f"vm_rss must be non-negative, got {self.vm_rss}")

        valid_statuses = ["R", "S", "D", "Z", "T", "W", "X", "I"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")

    @property
    def rss_mb(self) -> float:
        """Get RSS in MB"""
        return round(self.vm_rss / (1024 * 1024), 2)

    @property
    def vms_mb(self) -> float:
        """Get VMS in MB"""
        return round(self.vm_size / (1024 * 1024), 2)

    @property
    def swap_mb(self) -> float:
        """Get swap in MB"""
        return round(self.vm_swap / (1024 * 1024), 2)

    def to_dict(self):
        """Convert to dictionary for JSON/YAML output"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'pid': self.pid,
            'name': self.name,
            'rss_mb': self.rss_mb,
            'vms_mb': self.vms_mb,
            'swap_mb': self.swap_mb,
            'data_mb': round(self.vm_data / (1024 * 1024), 2),
            'stack_mb': round(self.vm_stk / (1024 * 1024), 2),
            'exe_mb': round(self.vm_exe / (1024 * 1024), 2),
            'lib_mb': round(self.vm_lib / (1024 * 1024), 2),
            'username': self.username,
            'status': self.status,
        }
