"""Log pattern data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class LogPattern:
    """Log pattern (template) data model."""

    template: str  # Log template with placeholders
    pattern_id: str  # Unique pattern identifier
    count: int  # Number of occurrences
    first_seen: datetime  # First occurrence timestamp
    last_seen: datetime  # Last occurrence timestamp

    # Optional fields
    example_messages: Optional[List[str]] = None  # Example log messages
    parameters: Optional[List[str]] = None  # List of parameter names
    severity_distribution: Optional[Dict[str, int]] = None  # Count by log level

    def __post_init__(self):
        """Validate log pattern."""
        if not self.template:
            raise ValueError("template cannot be empty")

        if not self.pattern_id:
            raise ValueError("pattern_id cannot be empty")

        if self.count < 0:
            raise ValueError("count must be non-negative")

        if self.first_seen > self.last_seen:
            raise ValueError("first_seen cannot be after last_seen")

    @property
    def frequency(self) -> float:
        """Calculate frequency (occurrences per second)."""
        duration = (self.last_seen - self.first_seen).total_seconds()
        if duration == 0:
            return float(self.count)
        return self.count / duration

    @property
    def is_rare(self) -> bool:
        """Check if pattern is rare (count <= 5)."""
        return self.count <= 5

    @property
    def is_common(self) -> bool:
        """Check if pattern is common (count >= 100)."""
        return self.count >= 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'template': self.template,
            'pattern_id': self.pattern_id,
            'count': self.count,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'example_messages': self.example_messages,
            'parameters': self.parameters,
            'severity_distribution': self.severity_distribution,
            'frequency': self.frequency,
            'is_rare': self.is_rare,
            'is_common': self.is_common,
        }
