"""Utility functions for AIOps CLI."""

import re
from datetime import datetime, timedelta
from typing import Tuple


def parse_time_range(time_str: str) -> timedelta:
    """
    Parse time range string to timedelta.

    Examples:
        "60s" -> 60 seconds
        "30m" -> 30 minutes
        "1h" -> 1 hour
        "7d" -> 7 days

    Args:
        time_str: Time range string (e.g., "1h", "30m", "60s")

    Returns:
        timedelta object

    Raises:
        ValueError: If time_str is invalid
    """
    from .constants import TIME_PATTERNS

    match = re.match(r"^(\d+)([smhd])$", time_str.lower())
    if not match:
        raise ValueError(
            f"Invalid time format: {time_str}. "
            f"Expected format: <number><unit> where unit is s, m, h, or d"
        )

    value, unit = match.groups()
    value = int(value)

    if unit not in TIME_PATTERNS:
        raise ValueError(f"Invalid time unit: {unit}. Must be s, m, h, or d")

    return timedelta(seconds=value * TIME_PATTERNS[unit])


def format_duration(duration_seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        duration_seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "5m 22s", "1h 30m")
    """
    if duration_seconds < 60:
        return f"{duration_seconds:.0f}s"

    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    seconds = int(duration_seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0:
        parts.append(f"{seconds}s")

    return " ".join(parts) if parts else "0s"


def calculate_cpu_percent(
    total_time: float, idle_time: float, prev_total: float = 0, prev_idle: float = 0
) -> float:
    """
    Calculate CPU percentage from /proc/stat values.

    Args:
        total_time: Total CPU time (user + nice + system + idle + iowait + ...)
        idle_time: Idle CPU time
        prev_total: Previous total time (for delta calculation)
        prev_idle: Previous idle time (for delta calculation)

    Returns:
        CPU usage percentage (0-100)
    """
    if prev_total > 0:
        # Calculate delta since last measurement
        total_delta = total_time - prev_total
        idle_delta = idle_time - prev_idle
    else:
        # No previous measurement, use absolute values
        total_delta = total_time
        idle_delta = idle_time

    if total_delta == 0:
        return 0.0

    cpu_percent = 100.0 * (1.0 - idle_delta / total_delta)
    return round(cpu_percent, 2)


def get_time_range(start_str: str, end_str: str) -> Tuple[datetime, datetime]:
    """
    Get datetime range from string representations.

    Args:
        start_str: Start time string (ISO format or relative)
        end_str: End time string (ISO format or "now")

    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    if end_str.lower() == "now":
        end_dt = datetime.now()
    else:
        end_dt = datetime.fromisoformat(end_str)

    try:
        start_dt = datetime.fromisoformat(start_str)
    except ValueError:
        # Try to parse as relative time
        offset = parse_time_range(start_str)
        start_dt = end_dt - offset

    return start_dt, end_dt
