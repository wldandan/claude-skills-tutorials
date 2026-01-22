"""Log parser for extracting structured information from log lines."""

import re
from datetime import datetime
from typing import Optional, Dict, Any
from aiops.logs.models import LogEntry, LogLevel


class LogParser:
    """Parse log lines into structured LogEntry objects."""

    # Common log patterns
    SYSLOG_PATTERN = re.compile(
        r'^(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+'
        r'(?P<hostname>\S+)\s+'
        r'(?P<process>\S+?)(\[(?P<pid>\d+)\])?:\s+'
        r'(?P<message>.+)$'
    )

    APACHE_PATTERN = re.compile(
        r'^(?P<ip>\S+)\s+\S+\s+\S+\s+'
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'"(?P<method>\S+)\s+(?P<path>\S+)\s+(?P<protocol>\S+)"\s+'
        r'(?P<status>\d+)\s+(?P<size>\S+)'
    )

    PYTHON_PATTERN = re.compile(
        r'^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s+'
        r'(?P<level>\w+)\s+'
        r'(?P<logger>\S+)\s+'
        r'(?P<message>.+)$'
    )

    GENERIC_PATTERN = re.compile(
        r'^(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+'
        r'(?:\[?(?P<level>DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL)\]?\s+)?'
        r'(?:\[?(?P<process>[^\]]+)\]?\s+)?'
        r'(?P<message>.+)$',
        re.IGNORECASE
    )

    def __init__(self):
        """Initialize log parser."""
        self.patterns = [
            ('python', self.PYTHON_PATTERN),
            ('generic', self.GENERIC_PATTERN),
            ('syslog', self.SYSLOG_PATTERN),
            ('apache', self.APACHE_PATTERN),
        ]

    def parse(self, line: str, source: str, line_number: Optional[int] = None) -> Optional[LogEntry]:
        """Parse a log line into a LogEntry.

        Args:
            line: Raw log line
            source: Log source identifier (file path)
            line_number: Line number in the file

        Returns:
            LogEntry object or None if parsing fails
        """
        line = line.strip()
        if not line:
            return None

        # Try each pattern
        for pattern_name, pattern in self.patterns:
            match = pattern.match(line)
            if match:
                return self._create_log_entry(match, pattern_name, line, source, line_number)

        # Fallback: create entry with minimal parsing
        return self._create_fallback_entry(line, source, line_number)

    def _create_log_entry(
        self,
        match: re.Match,
        pattern_name: str,
        line: str,
        source: str,
        line_number: Optional[int]
    ) -> LogEntry:
        """Create LogEntry from regex match.

        Args:
            match: Regex match object
            pattern_name: Name of the matched pattern
            line: Raw log line
            source: Log source
            line_number: Line number

        Returns:
            LogEntry object
        """
        groups = match.groupdict()

        # Parse timestamp
        timestamp = self._parse_timestamp(groups.get('timestamp'))

        # Extract level
        level = groups.get('level', 'INFO')
        if level:
            level = level.upper()
            # Normalize WARN to WARNING
            if level == 'WARN':
                level = 'WARNING'
        else:
            level = self._detect_level_from_message(groups.get('message', ''))

        # Extract message
        message = groups.get('message', line)

        # Extract process info
        process = groups.get('process') or groups.get('logger')
        pid = groups.get('pid')
        if pid:
            pid = int(pid)

        # Extract hostname
        hostname = groups.get('hostname')

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=source,
            process=process,
            pid=pid,
            hostname=hostname,
            raw_line=line,
            line_number=line_number,
        )

    def _create_fallback_entry(
        self,
        line: str,
        source: str,
        line_number: Optional[int]
    ) -> LogEntry:
        """Create LogEntry with minimal parsing when no pattern matches.

        Args:
            line: Raw log line
            source: Log source
            line_number: Line number

        Returns:
            LogEntry object
        """
        # Detect level from keywords
        level = self._detect_level_from_message(line)

        return LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=line,
            source=source,
            raw_line=line,
            line_number=line_number,
        )

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp string into datetime object.

        Args:
            timestamp_str: Timestamp string

        Returns:
            datetime object
        """
        if not timestamp_str:
            return datetime.now()

        # Try common timestamp formats
        formats = [
            '%Y-%m-%d %H:%M:%S,%f',  # Python logging
            '%Y-%m-%d %H:%M:%S.%f',  # Generic with microseconds
            '%Y-%m-%d %H:%M:%S',     # Generic
            '%Y-%m-%dT%H:%M:%S.%fZ', # ISO8601 with Z
            '%Y-%m-%dT%H:%M:%S%z',   # ISO8601 with timezone
            '%Y-%m-%dT%H:%M:%S',     # ISO8601
            '%b %d %H:%M:%S',        # Syslog (no year)
            '%d/%b/%Y:%H:%M:%S %z',  # Apache
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        # If syslog format (no year), add current year
        try:
            dt = datetime.strptime(timestamp_str, '%b %d %H:%M:%S')
            return dt.replace(year=datetime.now().year)
        except ValueError:
            pass

        # Fallback to current time
        return datetime.now()

    def _detect_level_from_message(self, message: str) -> str:
        """Detect log level from message content.

        Args:
            message: Log message

        Returns:
            Log level string
        """
        message_lower = message.lower()

        if any(keyword in message_lower for keyword in ['fatal', 'panic']):
            return LogLevel.FATAL.value
        elif any(keyword in message_lower for keyword in ['critical', 'crit']):
            return LogLevel.CRITICAL.value
        elif any(keyword in message_lower for keyword in ['error', 'err', 'exception', 'failed', 'failure']):
            return LogLevel.ERROR.value
        elif any(keyword in message_lower for keyword in ['warn', 'warning']):
            return LogLevel.WARNING.value
        elif any(keyword in message_lower for keyword in ['debug', 'trace']):
            return LogLevel.DEBUG.value
        else:
            return LogLevel.INFO.value
