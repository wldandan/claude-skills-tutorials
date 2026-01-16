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

        # Validate that components are within reasonable ranges
        for component_name, value in [
            ("cpu_user", self.cpu_user),
            ("cpu_system", self.cpu_system),
            ("cpu_idle", self.cpu_idle),
            ("cpu_iowait", self.cpu_iowait),
            ("cpu_steal", self.cpu_steal),
        ]:
            if not 0 <= value <= 100:
                raise ValueError(f"{component_name} must be between 0 and 100, got {value}")

        # Allow small floating point differences in component sum
        # Components may not sum exactly to cpu_percent due to:
        # - Rounding in calculations
        # - Additional CPU components (nice, irq, softirq, steal, guest, etc.)
        total_calculated = self.cpu_user + self.cpu_system + self.cpu_idle + self.cpu_iowait + self.cpu_steal
        if abs(self.cpu_percent - total_calculated) > 5.0:
            # Allow 5% tolerance for additional CPU time components
            raise ValueError(
                f"CPU components sum ({total_calculated:.2f}) differs significantly "
                f"from cpu_percent ({self.cpu_percent:.2f}). "
                f"This may indicate a calculation error."
            )
