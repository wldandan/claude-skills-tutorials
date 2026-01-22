"""Log entry data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class LogEntry:
    """Log entry data model."""

    timestamp: datetime
    level: str
    message: str
    source: str  # Log file path or source identifier

    # Optional fields
    process: Optional[str] = None
    pid: Optional[int] = None
    thread: Optional[str] = None
    hostname: Optional[str] = None
    raw_line: Optional[str] = None
    line_number: Optional[int] = None

    # Parsed fields
    template: Optional[str] = None  # Log template after parameter extraction
    parameters: Optional[Dict[str, Any]] = None  # Extracted parameters

    def __post_init__(self):
        """Validate log entry."""
        if not self.message:
            raise ValueError("message cannot be empty")

        if not self.source:
            raise ValueError("source cannot be empty")

        # Normalize log level
        self.level = self.level.upper()

        # Validate log level
        valid_levels = [level.value for level in LogLevel]
        if self.level not in valid_levels:
            self.level = LogLevel.UNKNOWN.value

    @property
    def is_error(self) -> bool:
        """Check if log entry is an error."""
        return self.level in [LogLevel.ERROR.value, LogLevel.CRITICAL.value, LogLevel.FATAL.value]

    @property
    def is_warning(self) -> bool:
        """Check if log entry is a warning."""
        return self.level == LogLevel.WARNING.value

    @property
    def severity_score(self) -> int:
        """Get severity score (higher = more severe)."""
        severity_map = {
            LogLevel.DEBUG.value: 0,
            LogLevel.INFO.value: 1,
            LogLevel.WARNING.value: 2,
            LogLevel.ERROR.value: 3,
            LogLevel.CRITICAL.value: 4,
            LogLevel.FATAL.value: 5,
            LogLevel.UNKNOWN.value: 0,
        }
        return severity_map.get(self.level, 0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'message': self.message,
            'source': self.source,
            'process': self.process,
            'pid': self.pid,
            'thread': self.thread,
            'hostname': self.hostname,
            'raw_line': self.raw_line,
            'line_number': self.line_number,
            'template': self.template,
            'parameters': self.parameters,
            'is_error': self.is_error,
            'is_warning': self.is_warning,
            'severity_score': self.severity_score,
        }
