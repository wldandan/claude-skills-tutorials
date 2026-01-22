"""Process status metrics data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List


@dataclass
class ProcessStatusMetric:
    """Process status metrics from psutil and /proc."""

    timestamp: datetime
    pid: int
    name: str
    status: str  # 'R', 'S', 'D', 'Z', 'T', 'W', 'X', 'I'

    # Resource usage
    cpu_percent: float
    memory_percent: float
    memory_rss: int  # Resident Set Size in bytes
    memory_vms: int  # Virtual Memory Size in bytes

    # Process info
    ppid: int  # Parent PID
    username: str
    create_time: float  # Unix timestamp
    num_threads: int
    num_fds: int  # Number of file descriptors

    # Status flags
    is_running: bool = True
    is_zombie: bool = False

    # Optional fields
    cmdline: Optional[List[str]] = None
    cwd: Optional[str] = None
    exe: Optional[str] = None

    def __post_init__(self):
        """Validate process status metric."""
        if self.pid <= 0:
            raise ValueError(f"Invalid PID: {self.pid}")

        valid_statuses = ['R', 'S', 'D', 'Z', 'T', 'W', 'X', 'I']
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {self.status}. Must be one of {valid_statuses}"
            )

        if self.cpu_percent < 0:
            raise ValueError("cpu_percent must be non-negative")

        if self.memory_percent < 0:
            raise ValueError("memory_percent must be non-negative")

        if self.memory_rss < 0:
            raise ValueError("memory_rss must be non-negative")

        if self.num_threads < 0:
            raise ValueError("num_threads must be non-negative")

        # Set zombie flag based on status
        self.is_zombie = (self.status == 'Z')

        # Set running flag
        self.is_running = (self.status in ['R', 'S'])

    @property
    def memory_rss_mb(self) -> float:
        """RSS in MB."""
        return self.memory_rss / (1024 * 1024)

    @property
    def memory_vms_mb(self) -> float:
        """VMS in MB."""
        return self.memory_vms / (1024 * 1024)

    @property
    def uptime_seconds(self) -> float:
        """Process uptime in seconds."""
        return datetime.now().timestamp() - self.create_time

    @property
    def is_sleeping(self) -> bool:
        """Check if process is sleeping."""
        return self.status == 'S'

    @property
    def is_disk_sleep(self) -> bool:
        """Check if process is in uninterruptible disk sleep."""
        return self.status == 'D'

    @property
    def is_stopped(self) -> bool:
        """Check if process is stopped."""
        return self.status == 'T'

    @property
    def cmdline_str(self) -> str:
        """Command line as string."""
        if self.cmdline:
            return ' '.join(self.cmdline)
        return ''

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'pid': self.pid,
            'name': self.name,
            'status': self.status,
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_rss': self.memory_rss,
            'memory_vms': self.memory_vms,
            'ppid': self.ppid,
            'username': self.username,
            'create_time': self.create_time,
            'num_threads': self.num_threads,
            'num_fds': self.num_fds,
            'is_running': self.is_running,
            'is_zombie': self.is_zombie,
            'cmdline': self.cmdline,
            'cwd': self.cwd,
            'exe': self.exe,
            'memory_rss_mb': self.memory_rss_mb,
            'memory_vms_mb': self.memory_vms_mb,
            'uptime_seconds': self.uptime_seconds,
            'is_sleeping': self.is_sleeping,
            'is_disk_sleep': self.is_disk_sleep,
            'is_stopped': self.is_stopped,
            'cmdline_str': self.cmdline_str,
        }
