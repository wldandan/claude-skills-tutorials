"""Data collectors for CPU metrics."""

from .system_cpu import SystemCPUCollector
from .process_cpu import ProcessCPUCollector

__all__ = [
    "SystemCPUCollector",
    "ProcessCPUCollector",
]
