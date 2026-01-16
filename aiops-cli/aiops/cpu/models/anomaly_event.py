"""Anomaly event data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AnomalyEvent:
    """An anomaly event detected by the system."""

    id: str
    timestamp: datetime
    end_time: Optional[datetime]
    severity: str  # 'warning', 'critical', 'emergency'
    type: str  # 'high_cpu', 'single_core_overload', 'process_spike', etc.
    confidence: float  # 0.0 to 1.0
    metrics: Dict[str, float]
    baseline: Optional[float]
    top_processes: List[Any]  # List of ProcessMetric
    algorithm: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate anomaly event."""
        valid_severities = ["warning", "critical", "emergency"]
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity: {self.severity}. Must be one of {valid_severities}"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get anomaly duration in seconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.timestamp).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/YAML output."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "severity": self.severity,
            "type": self.type,
            "confidence": self.confidence,
            "metrics": self.metrics,
            "baseline": self.baseline,
            "top_processes": [
                {
                    "pid": p.pid,
                    "name": p.name,
                    "cpu_percent": p.cpu_percent,
                    "user": p.username,
                }
                for p in self.top_processes
            ],
            "algorithm": self.algorithm,
            "metadata": self.metadata,
        }
