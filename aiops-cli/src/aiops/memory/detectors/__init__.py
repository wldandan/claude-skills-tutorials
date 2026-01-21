"""
Memory detectors for anomaly detection
"""
from aiops.memory.detectors.memory_leak import MemoryLeakDetector
from aiops.memory.detectors.oom_risk import OOMRiskDetector
from aiops.memory.detectors.swap_anomaly import SwapAnomalyDetector

__all__ = [
    'MemoryLeakDetector',
    'OOMRiskDetector',
    'SwapAnomalyDetector',
]
