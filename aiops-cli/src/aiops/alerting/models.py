"""Alert rule model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """Alert status."""
    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SILENCED = "silenced"


@dataclass
class AlertRule:
    """Alert rule definition."""

    name: str
    condition: str
    severity: str
    enabled: bool = True
    description: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)

    # Evaluation settings
    evaluation_interval: int = 60  # seconds
    for_duration: int = 0  # seconds (alert fires after condition is true for this duration)

    # Notification settings
    notification_channels: List[str] = field(default_factory=list)

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate alert rule."""
        if not self.name:
            raise ValueError("name cannot be empty")

        if not self.condition:
            raise ValueError("condition cannot be empty")

        valid_severities = [s.value for s in AlertSeverity]
        if self.severity not in valid_severities:
            raise ValueError(f"Invalid severity: {self.severity}")

        if self.evaluation_interval <= 0:
            raise ValueError("evaluation_interval must be positive")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'condition': self.condition,
            'severity': self.severity,
            'enabled': self.enabled,
            'description': self.description,
            'labels': self.labels,
            'annotations': self.annotations,
            'evaluation_interval': self.evaluation_interval,
            'for_duration': self.for_duration,
            'notification_channels': self.notification_channels,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class Alert:
    """Alert instance."""

    rule_name: str
    status: str
    severity: str
    message: str
    started_at: datetime

    # Optional fields
    ended_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate alert."""
        if not self.rule_name:
            raise ValueError("rule_name cannot be empty")

        valid_statuses = [s.value for s in AlertStatus]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rule_name': self.rule_name,
            'status': self.status,
            'severity': self.severity,
            'message': self.message,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'labels': self.labels,
            'annotations': self.annotations,
            'metrics': self.metrics,
        }
