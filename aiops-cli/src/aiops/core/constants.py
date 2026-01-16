"""Constants for AIOps CLI."""

from typing import List


# CPU metric names
CPU_METRICS = [
    "cpu_percent",
    "cpu_user",
    "cpu_system",
    "cpu_idle",
    "cpu_iowait",
    "cpu_steal",
]

# Severity levels
SEVERITY_LEVELS = ["warning", "critical", "emergency"]

# Anomaly types
ANOMALY_TYPES = [
    "high_cpu",
    "single_core_overload",
    "process_spike",
    "io_wait_high",
    "sustained_load",
]

# Output formats
OUTPUT_FORMATS = ["table", "json", "yaml"]

# Time format patterns
TIME_PATTERNS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}
