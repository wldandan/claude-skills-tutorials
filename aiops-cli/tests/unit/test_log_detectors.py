"""
Unit tests for log detectors
"""
import pytest
from datetime import datetime
from aiops.logs.models import LogEntry
from aiops.logs.detectors import LogLevelAnomalyDetector, LogVolumeAnomalyDetector


class TestLogLevelAnomalyDetector:
    """Test LogLevelAnomalyDetector"""

    def test_detect_high_error_rate(self):
        """Test detection of high error rate"""
        detector = LogLevelAnomalyDetector(error_threshold=5)
        detector.initialize()

        # Create logs with many errors
        logs = [
            LogEntry(
                timestamp=datetime.now(),
                level="ERROR",
                message=f"Error {i}",
                source="/var/log/app.log"
            )
            for i in range(10)
        ]

        events = detector.detect(logs)

        assert len(events) == 1
        assert events[0].type == 'high_error_rate'
        assert events[0].severity == 'critical'
        assert events[0].metrics['error_count'] == 10

        detector.cleanup()

    def test_detect_high_warning_rate(self):
        """Test detection of high warning rate"""
        detector = LogLevelAnomalyDetector(warning_threshold=20)
        detector.initialize()

        # Create logs with many warnings
        logs = [
            LogEntry(
                timestamp=datetime.now(),
                level="WARNING",
                message=f"Warning {i}",
                source="/var/log/app.log"
            )
            for i in range(30)
        ]

        events = detector.detect(logs)

        assert len(events) == 1
        assert events[0].type == 'high_warning_rate'
        assert events[0].severity == 'warning'
        assert events[0].metrics['warning_count'] == 30

        detector.cleanup()

    def test_no_anomaly(self):
        """Test when no anomaly exists"""
        detector = LogLevelAnomalyDetector()
        detector.initialize()

        # Create normal logs
        logs = [
            LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message=f"Info {i}",
                source="/var/log/app.log"
            )
            for i in range(5)
        ]

        events = detector.detect(logs)
        assert len(events) == 0

        detector.cleanup()


class TestLogVolumeAnomalyDetector:
    """Test LogVolumeAnomalyDetector"""

    def test_detect_log_storm(self):
        """Test detection of log storm"""
        detector = LogVolumeAnomalyDetector(volume_threshold=100)
        detector.initialize()

        # Create many logs
        logs = [
            LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message=f"Log {i}",
                source="/var/log/app.log"
            )
            for i in range(200)
        ]

        events = detector.detect(logs)

        assert len(events) == 1
        assert events[0].type == 'log_storm'
        assert events[0].severity == 'warning'
        assert events[0].metrics['log_volume'] == 200
        assert events[0].metrics['excess_ratio'] == 2.0

        detector.cleanup()

    def test_normal_volume(self):
        """Test normal log volume"""
        detector = LogVolumeAnomalyDetector(volume_threshold=100)
        detector.initialize()

        # Create normal volume of logs
        logs = [
            LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message=f"Log {i}",
                source="/var/log/app.log"
            )
            for i in range(50)
        ]

        events = detector.detect(logs)
        assert len(events) == 0

        detector.cleanup()
