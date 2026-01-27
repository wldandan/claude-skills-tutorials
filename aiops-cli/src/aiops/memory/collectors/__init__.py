"""Memory collectors."""

from aiops.memory.collectors.system_memory import SystemMemoryCollector
from aiops.memory.collectors.process_memory import ProcessMemoryCollector

__all__ = [
    'SystemMemoryCollector',
    'ProcessMemoryCollector',
]
