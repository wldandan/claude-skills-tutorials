"""Process detectors."""

from aiops.process.detectors.zombie_detector import ZombieProcessDetector
from aiops.process.detectors.crash_detector import ProcessCrashDetector
from aiops.process.detectors.resource_leak_detector import ResourceLeakDetector

__all__ = [
    'ZombieProcessDetector',
    'ProcessCrashDetector',
    'ResourceLeakDetector',
]
