"""
Unit tests for process status models
"""
import pytest
from datetime import datetime
from aiops.process.models import ProcessStatusMetric


class TestProcessStatusMetric:
    """Test ProcessStatusMetric model"""

    def test_create_valid_metric(self):
        """Test creating a valid process status metric"""
        metric = ProcessStatusMetric(
            timestamp=datetime.now(),
            pid=1234,
            name="python",
            status="R",
            cpu_percent=25.5,
            memory_percent=10.2,
            memory_rss=1024 * 1024 * 100,  # 100 MB
            memory_vms=1024 * 1024 * 200,  # 200 MB
            ppid=1,
            username="testuser",
            create_time=datetime.now().timestamp() - 3600,  # 1 hour ago
            num_threads=4,
            num_fds=10,
        )

        assert metric.pid == 1234
        assert metric.name == "python"
        assert metric.status == "R"
        assert metric.cpu_percent == 25.5
        assert metric.memory_percent == 10.2
        assert metric.is_running is True
        assert metric.is_zombie is False

    def test_invalid_pid(self):
        """Test that invalid PID raises ValueError"""
        with pytest.raises(ValueError, match="Invalid PID"):
            ProcessStatusMetric(
                timestamp=datetime.now(),
                pid=0,  # Invalid
                name="test",
                status="R",
                cpu_percent=0,
                memory_percent=0,
                memory_rss=0,
                memory_vms=0,
                ppid=1,
                username="test",
                create_time=datetime.now().timestamp(),
                num_threads=1,
                num_fds=0,
            )

    def test_invalid_status(self):
        """Test that invalid status raises ValueError"""
        with pytest.raises(ValueError, match="Invalid status"):
            ProcessStatusMetric(
                timestamp=datetime.now(),
                pid=1234,
                name="test",
                status="INVALID",  # Invalid status
                cpu_percent=0,
                memory_percent=0,
                memory_rss=0,
                memory_vms=0,
                ppid=1,
                username="test",
                create_time=datetime.now().timestamp(),
                num_threads=1,
                num_fds=0,
            )

    def test_negative_cpu_percent(self):
        """Test that negative CPU percent raises ValueError"""
        with pytest.raises(ValueError, match="cpu_percent must be non-negative"):
            ProcessStatusMetric(
                timestamp=datetime.now(),
                pid=1234,
                name="test",
                status="R",
                cpu_percent=-1.0,  # Invalid
                memory_percent=0,
                memory_rss=0,
                memory_vms=0,
                ppid=1,
                username="test",
                create_time=datetime.now().timestamp(),
                num_threads=1,
                num_fds=0,
            )

    def test_negative_memory_percent(self):
        """Test that negative memory percent raises ValueError"""
        with pytest.raises(ValueError, match="memory_percent must be non-negative"):
            ProcessStatusMetric(
                timestamp=datetime.now(),
                pid=1234,
                name="test",
                status="R",
                cpu_percent=0,
                memory_percent=-1.0,  # Invalid
                memory_rss=0,
                memory_vms=0,
                ppid=1,
                username="test",
                create_time=datetime.now().timestamp(),
                num_threads=1,
                num_fds=0,
            )

    def test_zombie_process(self):
        """Test zombie process detection"""
        metric = ProcessStatusMetric(
            timestamp=datetime.now(),
            pid=1234,
            name="zombie",
            status="Z",  # Zombie status
            cpu_percent=0,
            memory_percent=0,
            memory_rss=0,
            memory_vms=0,
            ppid=1,
            username="test",
            create_time=datetime.now().timestamp(),
            num_threads=0,
            num_fds=0,
        )

        assert metric.is_zombie is True
        assert metric.is_running is False

    def test_sleeping_process(self):
        """Test sleeping process detection"""
        metric = ProcessStatusMetric(
            timestamp=datetime.now(),
            pid=1234,
            name="sleeper",
            status="S",  # Sleeping
            cpu_percent=0,
            memory_percent=5.0,
            memory_rss=1024 * 1024 * 50,
            memory_vms=1024 * 1024 * 100,
            ppid=1,
            username="test",
            create_time=datetime.now().timestamp(),
            num_threads=1,
            num_fds=5,
        )

        assert metric.is_sleeping is True
        assert metric.is_running is True  # S is considered running
        assert metric.is_zombie is False

    def test_disk_sleep_process(self):
        """Test disk sleep process detection"""
        metric = ProcessStatusMetric(
            timestamp=datetime.now(),
            pid=1234,
            name="disk_io",
            status="D",  # Uninterruptible disk sleep
            cpu_percent=0,
            memory_percent=5.0,
            memory_rss=1024 * 1024 * 50,
            memory_vms=1024 * 1024 * 100,
            ppid=1,
            username="test",
            create_time=datetime.now().timestamp(),
            num_threads=1,
            num_fds=5,
        )

        assert metric.is_disk_sleep is True
        assert metric.is_running is False

    def test_stopped_process(self):
        """Test stopped process detection"""
        metric = ProcessStatusMetric(
            timestamp=datetime.now(),
            pid=1234,
            name="stopped",
            status="T",  # Stopped
            cpu_percent=0,
            memory_percent=5.0,
            memory_rss=1024 * 1024 * 50,
            memory_vms=1024 * 1024 * 100,
            ppid=1,
            username="test",
            create_time=datetime.now().timestamp(),
            num_threads=1,
            num_fds=5,
        )

        assert metric.is_stopped is True
        assert metric.is_running is False

    def test_memory_properties(self):
        """Test memory conversion properties"""
        metric = ProcessStatusMetric(
            timestamp=datetime.now(),
            pid=1234,
            name="test",
            status="R",
            cpu_percent=10.0,
            memory_percent=5.0,
            memory_rss=1024 * 1024 * 100,  # 100 MB
            memory_vms=1024 * 1024 * 200,  # 200 MB
            ppid=1,
            username="test",
            create_time=datetime.now().timestamp(),
            num_threads=1,
            num_fds=5,
        )

        assert metric.memory_rss_mb == pytest.approx(100.0, rel=0.01)
        assert metric.memory_vms_mb == pytest.approx(200.0, rel=0.01)

    def test_uptime_calculation(self):
        """Test uptime calculation"""
        create_time = datetime.now().timestamp() - 3600  # 1 hour ago
        metric = ProcessStatusMetric(
            timestamp=datetime.now(),
            pid=1234,
            name="test",
            status="R",
            cpu_percent=10.0,
            memory_percent=5.0,
            memory_rss=1024 * 1024 * 100,
            memory_vms=1024 * 1024 * 200,
            ppid=1,
            username="test",
            create_time=create_time,
            num_threads=1,
            num_fds=5,
        )

        # Uptime should be approximately 3600 seconds (1 hour)
        assert metric.uptime_seconds == pytest.approx(3600, abs=1)

    def test_cmdline_str(self):
        """Test command line string property"""
        metric = ProcessStatusMetric(
            timestamp=datetime.now(),
            pid=1234,
            name="python",
            status="R",
            cpu_percent=10.0,
            memory_percent=5.0,
            memory_rss=1024 * 1024 * 100,
            memory_vms=1024 * 1024 * 200,
            ppid=1,
            username="test",
            create_time=datetime.now().timestamp(),
            num_threads=1,
            num_fds=5,
            cmdline=["python", "script.py", "--arg", "value"],
        )

        assert metric.cmdline_str == "python script.py --arg value"

    def test_cmdline_str_none(self):
        """Test command line string when cmdline is None"""
        metric = ProcessStatusMetric(
            timestamp=datetime.now(),
            pid=1234,
            name="test",
            status="R",
            cpu_percent=10.0,
            memory_percent=5.0,
            memory_rss=1024 * 1024 * 100,
            memory_vms=1024 * 1024 * 200,
            ppid=1,
            username="test",
            create_time=datetime.now().timestamp(),
            num_threads=1,
            num_fds=5,
            cmdline=None,
        )

        assert metric.cmdline_str == ""

    def test_to_dict(self):
        """Test conversion to dictionary"""
        timestamp = datetime.now()
        create_time = timestamp.timestamp() - 3600
        metric = ProcessStatusMetric(
            timestamp=timestamp,
            pid=1234,
            name="python",
            status="R",
            cpu_percent=25.5,
            memory_percent=10.2,
            memory_rss=1024 * 1024 * 100,
            memory_vms=1024 * 1024 * 200,
            ppid=1,
            username="testuser",
            create_time=create_time,
            num_threads=4,
            num_fds=10,
            cmdline=["python", "script.py"],
            cwd="/home/test",
            exe="/usr/bin/python",
        )

        result = metric.to_dict()

        assert result['pid'] == 1234
        assert result['name'] == "python"
        assert result['status'] == "R"
        assert result['cpu_percent'] == 25.5
        assert result['memory_percent'] == 10.2
        assert result['memory_rss'] == 1024 * 1024 * 100
        assert result['memory_vms'] == 1024 * 1024 * 200
        assert result['ppid'] == 1
        assert result['username'] == "testuser"
        assert result['create_time'] == create_time
        assert result['num_threads'] == 4
        assert result['num_fds'] == 10
        assert result['is_running'] is True
        assert result['is_zombie'] is False
        assert result['cmdline'] == ["python", "script.py"]
        assert result['cwd'] == "/home/test"
        assert result['exe'] == "/usr/bin/python"
        assert result['memory_rss_mb'] == pytest.approx(100.0, rel=0.01)
        assert result['memory_vms_mb'] == pytest.approx(200.0, rel=0.01)
        assert result['uptime_seconds'] == pytest.approx(3600, abs=1)
        assert result['is_sleeping'] is False
        assert result['is_disk_sleep'] is False
        assert result['is_stopped'] is False
        assert result['cmdline_str'] == "python script.py"
