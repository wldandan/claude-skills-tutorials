"""Log collector for reading and parsing log files."""

import os
from typing import List, Optional, Generator
from pathlib import Path
from aiops.core import BaseCollector
from aiops.logs.models import LogEntry
from aiops.logs.parsers import LogParser
from aiops.core.exceptions import CollectionError


class LogCollector(BaseCollector):
    """Collects and parses log entries from files."""

    def __init__(
        self,
        log_paths: List[str],
        level_filter: Optional[str] = None,
        tail: Optional[int] = None,
        follow: bool = False
    ):
        """
        Initialize the log collector.

        Args:
            log_paths: List of log file paths to collect from
            level_filter: Filter by log level (e.g., 'ERROR', 'WARNING')
            tail: Number of lines to read from end of file (like tail -n)
            follow: Follow mode (like tail -f)
        """
        self.log_paths = log_paths
        self.level_filter = level_filter.upper() if level_filter else None
        self.tail = tail
        self.follow = follow
        self.parser = LogParser()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the collector."""
        # Verify log files exist
        for log_path in self.log_paths:
            path = Path(log_path)
            if not path.exists():
                raise CollectionError(f"Log file not found: {log_path}")
            if not path.is_file():
                raise CollectionError(f"Not a file: {log_path}")
            if not os.access(log_path, os.R_OK):
                raise CollectionError(f"Cannot read file: {log_path}")

        self._initialized = True

    def collect(self) -> List[LogEntry]:
        """Collect log entries from all configured log files.

        Returns:
            List of LogEntry objects
        """
        if not self._initialized:
            raise CollectionError("Collector not initialized")

        entries = []
        for log_path in self.log_paths:
            entries.extend(self._collect_from_file(log_path))

        return entries

    def _collect_from_file(self, log_path: str) -> List[LogEntry]:
        """Collect log entries from a single file.

        Args:
            log_path: Path to log file

        Returns:
            List of LogEntry objects
        """
        entries = []

        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

                # Apply tail if specified
                if self.tail:
                    lines = lines[-self.tail:]

                # Parse each line
                for line_number, line in enumerate(lines, start=1):
                    entry = self.parser.parse(line, log_path, line_number)
                    if entry and self._matches_filter(entry):
                        entries.append(entry)

        except Exception as e:
            raise CollectionError(f"Failed to read log file {log_path}: {str(e)}")

        return entries

    def stream(self) -> Generator[LogEntry, None, None]:
        """Stream log entries in real-time (follow mode).

        Yields:
            LogEntry objects as they are read
        """
        if not self._initialized:
            raise CollectionError("Collector not initialized")

        if not self.follow:
            raise CollectionError("Stream mode requires follow=True")

        # For simplicity, we'll implement a basic version
        # In production, you'd use inotify or similar for efficient tailing
        import time

        file_positions = {path: 0 for path in self.log_paths}

        try:
            while True:
                for log_path in self.log_paths:
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            # Seek to last position
                            f.seek(file_positions[log_path])

                            # Read new lines
                            for line in f:
                                entry = self.parser.parse(line, log_path)
                                if entry and self._matches_filter(entry):
                                    yield entry

                            # Update position
                            file_positions[log_path] = f.tell()

                    except FileNotFoundError:
                        # File might have been rotated
                        file_positions[log_path] = 0
                    except Exception:
                        # Continue with other files
                        continue

                # Sleep briefly before next check
                time.sleep(0.1)

        except KeyboardInterrupt:
            return

    def _matches_filter(self, entry: LogEntry) -> bool:
        """Check if log entry matches the level filter.

        Args:
            entry: LogEntry to check

        Returns:
            True if entry matches filter or no filter is set
        """
        if not self.level_filter:
            return True

        return entry.level == self.level_filter

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
