"""CPU metric data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class CPUMetric:
    """System-level CPU metric."""

    timestamp: datetime
    cpu_percent: float
    cpu_user: float
    cpu_system: float
    cpu_idle: float
    cpu_iowait: float
    cpu_steal: float = 0.0
    per_cpu_percent: List[float] = field(default_factory=list)

    def __post_init__(self):
        """Validate CPU metrics."""
        if not 0 <= self.cpu_percent <= 100:
            raise ValueError(f"cpu_percent must be between 0 and 100, got {self.cpu_percent}")

        if self.cpu_percent != self.cpu_user + self.cpu_system + self.cpu_idle + self.cpu_iowait:
            # Allow small floating point errors
            total = self.cpu_user + self.cpu_system + self.cpu_idle + self.cpu_iowait
            if abs(self.cpu_percent - total) > 1.0:
                raise ValueError(
                    f"CPU components don't sum to cpu_percent: "
                    f"{self.cpu_percent} vs {total:.2f}"
                )
