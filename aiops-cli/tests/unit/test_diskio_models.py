#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Disk I/O 数据采集器和模型单元测试

测试内容:
1. Disk I/O 数据模型
2. Disk I/O 数据采集
3. Process I/O 数据采集
"""

import pytest
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from aiops.diskio.models import DiskIOMetric, ProcessIOMetric


class TestDiskIOMetric:
    """Disk I/O 指标模型测试"""

    def test_diskio_metric_creation(self):
        """测试 Disk I/O 指标对象创建"""
        timestamp = datetime.now()
        metric = DiskIOMetric(
            timestamp=timestamp,
            device="sda",
            reads_completed=1000,
            reads_merged=50,
            sectors_read=20000,
            time_reading_ms=5000,
            writes_completed=500,
            writes_merged=25,
            sectors_written=10000,
            time_writing_ms=2500,
            io_in_progress=2,
            time_io_ms=7500,
            weighted_time_io_ms=8000,
        )

        assert metric.device == "sda"
        assert metric.reads_completed == 1000
        assert metric.writes_completed == 500

    def test_diskio_metric_properties(self):
        """测试 Disk I/O 指标属性计算"""
        metric = DiskIOMetric(
            timestamp=datetime.now(),
            device="sda",
            reads_completed=1000,
            reads_merged=50,
            sectors_read=20000,  # 20000 * 512 = 10,240,000 bytes
            time_reading_ms=5000,
            writes_completed=500,
            writes_merged=25,
            sectors_written=10000,  # 10000 * 512 = 5,120,000 bytes
            time_writing_ms=2500,
            io_in_progress=2,
            time_io_ms=7500,
            weighted_time_io_ms=8000,
        )

        # Test read_bytes
        assert metric.read_bytes == 20000 * 512

        # Test write_bytes
        assert metric.write_bytes == 10000 * 512

        # Test total_io_operations
        assert metric.total_io_operations == 1500

        # Test avg_read_time_ms
        assert metric.avg_read_time_ms == pytest.approx(5.0, abs=0.1)

        # Test avg_write_time_ms
        assert metric.avg_write_time_ms == pytest.approx(5.0, abs=0.1)

    def test_diskio_metric_validation(self):
        """测试 Disk I/O 指标验证"""
        # Test empty device name
        with pytest.raises(ValueError):
            DiskIOMetric(
                timestamp=datetime.now(),
                device="",
                reads_completed=0,
                reads_merged=0,
                sectors_read=0,
                time_reading_ms=0,
                writes_completed=0,
                writes_merged=0,
                sectors_written=0,
                time_writing_ms=0,
                io_in_progress=0,
                time_io_ms=0,
                weighted_time_io_ms=0,
            )

        # Test negative values
        with pytest.raises(ValueError):
            DiskIOMetric(
                timestamp=datetime.now(),
                device="sda",
                reads_completed=-1,
                reads_merged=0,
                sectors_read=0,
                time_reading_ms=0,
                writes_completed=0,
                writes_merged=0,
                sectors_written=0,
                time_writing_ms=0,
                io_in_progress=0,
                time_io_ms=0,
                weighted_time_io_ms=0,
            )

    def test_diskio_metric_to_dict(self):
        """测试 Disk I/O 指标转换为字典"""
        timestamp = datetime.now()
        metric = DiskIOMetric(
            timestamp=timestamp,
            device="sda",
            reads_completed=1000,
            reads_merged=50,
            sectors_read=20000,
            time_reading_ms=5000,
            writes_completed=500,
            writes_merged=25,
            sectors_written=10000,
            time_writing_ms=2500,
            io_in_progress=2,
            time_io_ms=7500,
            weighted_time_io_ms=8000,
        )

        metric_dict = metric.to_dict()
        assert metric_dict['device'] == "sda"
        assert metric_dict['reads_completed'] == 1000
        assert metric_dict['writes_completed'] == 500
        assert 'read_bytes' in metric_dict
        assert 'write_bytes' in metric_dict


class TestProcessIOMetric:
    """Process I/O 指标模型测试"""

    def test_process_io_metric_creation(self):
        """测试 Process I/O 指标对象创建"""
        timestamp = datetime.now()
        metric = ProcessIOMetric(
            timestamp=timestamp,
            pid=1234,
            name="test_process",
            rchar=1000000,
            wchar=500000,
            syscr=100,
            syscw=50,
            read_bytes=800000,
            write_bytes=400000,
            cancelled_write_bytes=10000,
            username="testuser",
            status="R",
        )

        assert metric.pid == 1234
        assert metric.name == "test_process"
        assert metric.read_bytes == 800000
        assert metric.write_bytes == 400000

    def test_process_io_metric_properties(self):
        """测试 Process I/O 指标属性计算"""
        metric = ProcessIOMetric(
            timestamp=datetime.now(),
            pid=1234,
            name="test_process",
            rchar=1000000,
            wchar=500000,
            syscr=100,
            syscw=50,
            read_bytes=1048576,  # 1 MB
            write_bytes=2097152,  # 2 MB
            cancelled_write_bytes=10000,
            username="testuser",
            status="R",
        )

        # Test read_bytes_mb
        assert metric.read_bytes_mb == pytest.approx(1.0, abs=0.01)

        # Test write_bytes_mb
        assert metric.write_bytes_mb == pytest.approx(2.0, abs=0.01)

        # Test total_io_bytes
        assert metric.total_io_bytes == 1048576 + 2097152

        # Test total_io_mb
        assert metric.total_io_mb == pytest.approx(3.0, abs=0.01)

        # Test avg_read_syscall_bytes
        assert metric.avg_read_syscall_bytes == pytest.approx(10485.76, abs=0.1)

        # Test avg_write_syscall_bytes
        assert metric.avg_write_syscall_bytes == pytest.approx(41943.04, abs=0.1)

    def test_process_io_metric_validation(self):
        """测试 Process I/O 指标验证"""
        # Test invalid PID
        with pytest.raises(ValueError):
            ProcessIOMetric(
                timestamp=datetime.now(),
                pid=0,
                name="test",
                rchar=0,
                wchar=0,
                syscr=0,
                syscw=0,
                read_bytes=0,
                write_bytes=0,
                cancelled_write_bytes=0,
            )

        # Test negative values
        with pytest.raises(ValueError):
            ProcessIOMetric(
                timestamp=datetime.now(),
                pid=1234,
                name="test",
                rchar=-1,
                wchar=0,
                syscr=0,
                syscw=0,
                read_bytes=0,
                write_bytes=0,
                cancelled_write_bytes=0,
            )

    def test_process_io_metric_to_dict(self):
        """测试 Process I/O 指标转换为字典"""
        timestamp = datetime.now()
        metric = ProcessIOMetric(
            timestamp=timestamp,
            pid=1234,
            name="test_process",
            rchar=1000000,
            wchar=500000,
            syscr=100,
            syscw=50,
            read_bytes=800000,
            write_bytes=400000,
            cancelled_write_bytes=10000,
            username="testuser",
            status="R",
        )

        metric_dict = metric.to_dict()
        assert metric_dict['pid'] == 1234
        assert metric_dict['name'] == "test_process"
        assert 'read_bytes_mb' in metric_dict
        assert 'write_bytes_mb' in metric_dict
        assert 'total_io_mb' in metric_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
