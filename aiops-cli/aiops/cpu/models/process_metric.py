"""Process metric data model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProcessMetric:
    """Process-level CPU metric."""

    timestamp: datetime
    pid: int
    name: str
    cpu_percent: float
    user_time: float
    system_time: float
    num_threads: int
    status: str
    memory_percent: float
    username: str

    def __post_init__(self):
        """Validate process metrics."""
        if self.pid <= 0:
            raise ValueError(f"pid must be positive, got {self.pid}")

        if not 0 <= self.cpu_percent <= 100:
            raise ValueError(f"cpu_percent must be between 0 and 100, got {self.cpu_percent}")

        if not 0 <= self.memory_percent <= 100:
            raise ValueError(
                f"memory_percent must be between 0 and 100, got {self.memory_percent}"
            )

        valid_statuses = ["R", "S", "D", "Z", "T", "W", "X", "I"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")
