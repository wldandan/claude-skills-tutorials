"""
Unit tests for process detectors
"""
import pytest
from datetime import datetime
from aiops.process.models import ProcessStatusMetric
from aiops.process.detectors import (
    ZombieProcessDetector,
    ProcessCrashDetector,
    ResourceLeakDetector,
)


class TestZombieProcessDetector:
    """Test ZombieProcessDetector"""

    def test_detect_zombie_processes(self):
        """Test zombie process detection"""
        detector = ZombieProcessDetector()
        detector.initialize()

        # Create test metrics with zombie process
        metrics = [
            ProcessStatusMetric(
                timestamp=datetime.now(),
                pid=1234,
                name="zombie",
                status="Z",  # Zombie
                cpu_percent=0,
                memory_percent=0,
                memory_rss=0,
                memory_vms=0,
                ppid=1,
                username="test",
                create_time=datetime.now().timestamp(),
                num_threads=0,
                num_fds=0,
            ),
            ProcessStatusMetric(
                timestamp=datetime.now(),
                pid=5678,
                name="normal",
                status="S",  # Sleeping
                cpu_percent=5.0,
                memory_percent=2.0,
                memory_rss=1024 * 1024 * 100,
                memory_vms=1024 * 1024 * 200,
                ppid=1,
                username="test",
                create_time=datetime.now().timestamp(),
                num_threads=1,
                num_fds=10,
            ),
        ]

        events = detector.detect(metrics)

        assert len(events) == 1
        assert events[0].type == 'zombie_process'
        assert events[0].severity == 'warning'
        assert events[0].metrics['zombie_count'] == 1
        assert 1234 in events[0].metrics['zombie_pids']

        detector.cleanup()

    def test_no_zombies(self):
        """Test when no zombie processes exist"""
        detector = ZombieProcessDetector()
        detector.initialize()

        metrics = [
            ProcessStatusMetric(
                timestamp=datetime.now(),
                pid=1234,
                name="normal",
                status="S",
                cpu_percent=5.0,
                memory_percent=2.0,
                memory_rss=1024 * 1024 * 100,
                memory_vms=1024 * 1024 * 200,
                ppid=1,
                username="test",
                create_time=datetime.now().timestamp(),
                num_threads=1,
                num_fds=10,
            ),
        ]

        events = detector.detect(metrics)
        assert len(events) == 0

        detector.cleanup()


class TestProcessCrashDetector:
    """Test ProcessCrashDetector"""

    def test_detect_disappeared_process(self):
        """Test detection of disappeared processes"""
        detector = ProcessCrashDetector()
        detector.initialize()

        # First collection
        metrics1 = [
            ProcessStatusMetric(
                timestamp=datetime.now(),
                pid=1234,
                name="app",
                status="S",
                cpu_percent=5.0,
                memory_percent=2.0,
                memory_rss=1024 * 1024 * 100,
                memory_vms=1024 * 1024 * 200,
                ppid=1,
                username="test",
                create_time=datetime.now().timestamp(),
                num_threads=1,
                num_fds=10,
            ),
        ]

        events1 = detector.detect(metrics1)
        assert len(events1) == 0  # No previous state

        # Second collection - process disappeared
        metrics2 = []
        events2 = detector.detect(metrics2)

        assert len(events2) == 1
        assert events2[0].type == 'process_crash'
        assert events2[0].severity == 'critical'
        assert 1234 in events2[0].metrics['disappeared_pids']

        detector.cleanup()


class TestResourceLeakDetector:
    """Test ResourceLeakDetector"""

    def test_detect_memory_leak(self):
        """Test memory leak detection"""
        detector = ResourceLeakDetector(
            memory_growth_threshold_mb=50.0,
            min_samples=3
        )
        detector.initialize()

        # Simulate growing memory usage
        base_memory = 100 * 1024 * 1024  # 100 MB
        for i in range(5):
            metrics = [
                ProcessStatusMetric(
                    timestamp=datetime.now(),
                    pid=1234,
                    name="leaky_app",
                    status="S",
                    cpu_percent=5.0,
                    memory_percent=2.0,
                    memory_rss=base_memory + (i * 20 * 1024 * 1024),  # +20 MB each time
                    memory_vms=1024 * 1024 * 200,
                    ppid=1,
                    username="test",
                    create_time=datetime.now().timestamp(),
                    num_threads=1,
                    num_fds=10,
                ),
            ]
            events = detector.detect(metrics)

        # Should detect leak after enough samples
        assert len(events) > 0
        leak_events = [e for e in events if e.type == 'memory_leak']
        assert len(leak_events) > 0
        assert leak_events[0].metrics['pid'] == 1234

        detector.cleanup()

    def test_no_leak(self):
        """Test when no leak exists"""
        detector = ResourceLeakDetector(min_samples=3)
        detector.initialize()

        # Stable memory usage
        for i in range(5):
            metrics = [
                ProcessStatusMetric(
                    timestamp=datetime.now(),
                    pid=1234,
                    name="stable_app",
                    status="S",
                    cpu_percent=5.0,
                    memory_percent=2.0,
                    memory_rss=100 * 1024 * 1024,  # Constant
                    memory_vms=200 * 1024 * 1024,
                    ppid=1,
                    username="test",
                    create_time=datetime.now().timestamp(),
                    num_threads=1,
                    num_fds=10,
                ),
            ]
            events = detector.detect(metrics)

        # Should not detect leak
        leak_events = [e for e in events if e.type == 'memory_leak']
        assert len(leak_events) == 0

        detector.cleanup()
