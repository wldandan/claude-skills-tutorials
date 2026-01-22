"""
Unit tests for log models
"""
import pytest
from datetime import datetime
from aiops.logs.models import LogEntry, LogLevel, LogPattern


class TestLogEntry:
    """Test LogEntry model"""

    def test_create_valid_entry(self):
        """Test creating a valid log entry"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            message="Test message",
            source="/var/log/test.log",
        )

        assert entry.level == "INFO"
        assert entry.message == "Test message"
        assert entry.source == "/var/log/test.log"

    def test_empty_message(self):
        """Test that empty message raises ValueError"""
        with pytest.raises(ValueError, match="message cannot be empty"):
            LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message="",
                source="/var/log/test.log",
            )

    def test_empty_source(self):
        """Test that empty source raises ValueError"""
        with pytest.raises(ValueError, match="source cannot be empty"):
            LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message="Test",
                source="",
            )

    def test_level_normalization(self):
        """Test log level normalization"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level="info",
            message="Test",
            source="/var/log/test.log",
        )
        assert entry.level == "INFO"

    def test_invalid_level(self):
        """Test invalid log level defaults to UNKNOWN"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level="INVALID",
            message="Test",
            source="/var/log/test.log",
        )
        assert entry.level == "UNKNOWN"

    def test_is_error(self):
        """Test error detection"""
        error_entry = LogEntry(
            timestamp=datetime.now(),
            level="ERROR",
            message="Error message",
            source="/var/log/test.log",
        )
        assert error_entry.is_error is True

        info_entry = LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            message="Info message",
            source="/var/log/test.log",
        )
        assert info_entry.is_error is False

    def test_is_warning(self):
        """Test warning detection"""
        warning_entry = LogEntry(
            timestamp=datetime.now(),
            level="WARNING",
            message="Warning message",
            source="/var/log/test.log",
        )
        assert warning_entry.is_warning is True

    def test_severity_score(self):
        """Test severity score calculation"""
        debug_entry = LogEntry(
            timestamp=datetime.now(),
            level="DEBUG",
            message="Debug",
            source="/var/log/test.log",
        )
        assert debug_entry.severity_score == 0

        error_entry = LogEntry(
            timestamp=datetime.now(),
            level="ERROR",
            message="Error",
            source="/var/log/test.log",
        )
        assert error_entry.severity_score == 3

        fatal_entry = LogEntry(
            timestamp=datetime.now(),
            level="FATAL",
            message="Fatal",
            source="/var/log/test.log",
        )
        assert fatal_entry.severity_score == 5

    def test_to_dict(self):
        """Test conversion to dictionary"""
        timestamp = datetime.now()
        entry = LogEntry(
            timestamp=timestamp,
            level="ERROR",
            message="Test error",
            source="/var/log/test.log",
            process="test-app",
            pid=1234,
        )

        result = entry.to_dict()

        assert result['level'] == "ERROR"
        assert result['message'] == "Test error"
        assert result['source'] == "/var/log/test.log"
        assert result['process'] == "test-app"
        assert result['pid'] == 1234
        assert result['is_error'] is True
        assert result['severity_score'] == 3


class TestLogPattern:
    """Test LogPattern model"""

    def test_create_valid_pattern(self):
        """Test creating a valid log pattern"""
        now = datetime.now()
        pattern = LogPattern(
            template="User <*> logged in",
            pattern_id="pattern_001",
            count=100,
            first_seen=now,
            last_seen=now,
        )

        assert pattern.template == "User <*> logged in"
        assert pattern.pattern_id == "pattern_001"
        assert pattern.count == 100

    def test_empty_template(self):
        """Test that empty template raises ValueError"""
        with pytest.raises(ValueError, match="template cannot be empty"):
            LogPattern(
                template="",
                pattern_id="pattern_001",
                count=10,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
            )

    def test_empty_pattern_id(self):
        """Test that empty pattern_id raises ValueError"""
        with pytest.raises(ValueError, match="pattern_id cannot be empty"):
            LogPattern(
                template="Test",
                pattern_id="",
                count=10,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
            )

    def test_negative_count(self):
        """Test that negative count raises ValueError"""
        with pytest.raises(ValueError, match="count must be non-negative"):
            LogPattern(
                template="Test",
                pattern_id="pattern_001",
                count=-1,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
            )

    def test_invalid_time_range(self):
        """Test that first_seen after last_seen raises ValueError"""
        now = datetime.now()
        with pytest.raises(ValueError, match="first_seen cannot be after last_seen"):
            LogPattern(
                template="Test",
                pattern_id="pattern_001",
                count=10,
                first_seen=now,
                last_seen=datetime(2020, 1, 1),
            )

    def test_frequency_calculation(self):
        """Test frequency calculation"""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 12, 1, 0)  # 60 seconds later
        pattern = LogPattern(
            template="Test",
            pattern_id="pattern_001",
            count=60,
            first_seen=start,
            last_seen=end,
        )

        assert pattern.frequency == pytest.approx(1.0, rel=0.01)  # 1 per second

    def test_is_rare(self):
        """Test rare pattern detection"""
        pattern = LogPattern(
            template="Test",
            pattern_id="pattern_001",
            count=3,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        assert pattern.is_rare is True

        pattern2 = LogPattern(
            template="Test",
            pattern_id="pattern_002",
            count=100,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        assert pattern2.is_rare is False

    def test_is_common(self):
        """Test common pattern detection"""
        pattern = LogPattern(
            template="Test",
            pattern_id="pattern_001",
            count=150,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        assert pattern.is_common is True

        pattern2 = LogPattern(
            template="Test",
            pattern_id="pattern_002",
            count=50,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        assert pattern2.is_common is False

    def test_to_dict(self):
        """Test conversion to dictionary"""
        now = datetime.now()
        pattern = LogPattern(
            template="User <*> logged in",
            pattern_id="pattern_001",
            count=100,
            first_seen=now,
            last_seen=now,
            example_messages=["User alice logged in", "User bob logged in"],
            parameters=["username"],
        )

        result = pattern.to_dict()

        assert result['template'] == "User <*> logged in"
        assert result['pattern_id'] == "pattern_001"
        assert result['count'] == 100
        assert result['example_messages'] == ["User alice logged in", "User bob logged in"]
        assert result['parameters'] == ["username"]
