"""Process memory metric model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class ProcessMemoryMetric:
    """Process-level memory metrics from /proc/<pid>/status."""

    timestamp: datetime
    pid: int
    name: str

    # Memory sizes (KB)
    vm_size: int  # Virtual memory size
    vm_rss: int   # Resident set size
    vm_data: int  # Data segment size
    vm_stk: int   # Stack size
    vm_exe: int   # Executable size
    vm_lib: int   # Library size
    vm_swap: int  # Swap usage

    # Additional info
    username: Optional[str] = None
    status: Optional[str] = None

    def __post_init__(self):
        """Validate process memory metric."""
        if self.pid <= 0:
            raise ValueError("pid must be positive")

        if self.vm_size < 0:
            raise ValueError("vm_size cannot be negative")

        if self.vm_rss < 0:
            raise ValueError("vm_rss cannot be negative")

        if self.vm_swap < 0:
            raise ValueError("vm_swap cannot be negative")

    @property
    def rss_mb(self) -> float:
        """RSS in MB."""
        return self.vm_rss / 1024

    @property
    def vms_mb(self) -> float:
        """VMS in MB."""
        return self.vm_size / 1024

    @property
    def swap_mb(self) -> float:
        """Swap in MB."""
        return self.vm_swap / 1024

    @property
    def rss_percent(self) -> float:
        """RSS as percentage of VMS."""
        if self.vm_size == 0:
            return 0.0
        return (self.vm_rss / self.vm_size) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'pid': self.pid,
            'name': self.name,
            'vm_size': self.vm_size,
            'vm_rss': self.vm_rss,
            'vm_data': self.vm_data,
            'vm_stk': self.vm_stk,
            'vm_exe': self.vm_exe,
            'vm_lib': self.vm_lib,
            'vm_swap': self.vm_swap,
            'rss_mb': self.rss_mb,
            'vms_mb': self.vms_mb,
            'swap_mb': self.swap_mb,
            'rss_percent': self.rss_percent,
            'username': self.username,
            'status': self.status,
        }
