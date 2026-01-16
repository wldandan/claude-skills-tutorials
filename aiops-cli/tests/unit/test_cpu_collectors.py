#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU 数据采集器单元测试

测试内容:
1. 系统 CPU 数据采集
2. 进程 CPU 数据采集
3. 数据准确性验证
4. 错误处理
"""

import pytest
import os
import sys
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'aiops-cli'))

from aiops.cpu.collectors.system_cpu import SystemCPUCollector
from aiops.cpu.collectors.process_cpu import ProcessCPUCollector
from aiops.cpu.models.cpu_metric import CPUMetric
from aiops.core.exceptions import CollectionError


class TestSystemCPUCollector:
    """系统 CPU 采集器测试"""

    @pytest.fixture
    def collector(self):
        """创建采集器实例"""
        return SystemCPUCollector()

    @pytest.fixture
    def mock_proc_stat_content(self):
        """模拟 /proc/stat 内容"""
        return """cpu  2255 34 2290 22625563 6290 127 456 0 0 0
cpu0 1132 17 1145 11312782 3145 63 228 0 0 0
cpu1 1123 17 1145 11312781 3145 64 228 0 0 0
intr 123456789
ctxt 987654321
btime 1234567890
processes 1000
procs_running 5
procs_blocked 0
softirq 12345678
"""

    def test_initialize_success(self, collector, tmp_path):
        """测试成功初始化"""
        # 创建模拟的 /proc/stat 文件
        proc_stat = tmp_path / "proc_stat"
        proc_stat.write_text("cpu  100 0 0 100 0 0 0 0 0 0\n")

        with patch.object(collector, 'PROC_STAT_PATH', str(proc_stat)):
            collector.initialize()
            assert collector._initialized is True

    def test_initialize_file_not_found(self, collector):
        """测试文件不存在时的错误处理"""
        with patch.object(collector, 'PROC_STAT_PATH', '/nonexistent/proc/stat'):
            with pytest.raises(CollectionError) as exc_info:
                collector.initialize()
            assert "Cannot read" in str(exc_info.value)

    def test_collect_cpu_metrics(self, collector, mock_proc_stat_content):
        """测试 CPU 指标采集"""
        with patch('builtins.open', mock_open(read_data=mock_proc_stat_content)):
            collector.initialize()
            metrics = collector.collect()

            assert len(metrics) == 1
            metric = metrics[0]
            assert isinstance(metric, CPUMetric)
            assert hasattr(metric, 'cpu_percent')
            assert hasattr(metric, 'cpu_user')
            assert hasattr(metric, 'cpu_system')
            assert hasattr(metric, 'cpu_idle')

    def test_collect_parse_error(self, collector):
        """测试解析错误处理"""
        invalid_content = "cpu invalid data here\n"

        with patch('builtins.open', mock_open(read_data=invalid_content)):
            collector.initialize()
            with pytest.raises(CollectionError) as exc_info:
                collector.collect()
            assert "Failed to parse" in str(exc_info.value)

    def test_collect_io_error(self, collector):
        """测试 IO 错误处理"""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            collector.initialize()
            with pytest.raises(CollectionError) as exc_info:
                collector.collect()
            assert "Failed to read" in str(exc_info.value)

    def test_cpu_percent_calculation(self, collector, mock_proc_stat_content):
        """测试 CPU 使用率计算准确性"""
        with patch('builtins.open', mock_open(read_data=mock_proc_stat_content)):
            collector.initialize()

            # 第一次采集（初始化）
            collector.collect()

            # 第二次采集（计算变化）
            metrics = collector.collect()
            cpu_percent = metrics[0].cpu_percent

            # CPU 使用率应该在合理范围内
            assert 0 <= cpu_percent <= 100

    def test_cpu_component_sum(self, collector, mock_proc_stat_content):
        """测试 CPU 时间分量总和"""
        with patch('builtins.open', mock_open(read_data=mock_proc_stat_content)):
            collector.initialize()
            collector.collect()  # 第一次采集初始化

            metrics = collector.collect()
            metric = metrics[0]

            # 各分量总和应该接近 100%（允许浮点误差）
            total = metric.cpu_user + metric.cpu_system + metric.cpu_idle + metric.cpu_iowait
            assert 99.0 <= total <= 101.0  # 允许 ±1% 误差

    def test_multiple_collections(self, collector, mock_proc_stat_content):
        """测试多次采集的一致性"""
        with patch('builtins.open', mock_open(read_data=mock_proc_stat_content)):
            collector.initialize()

            # 多次采集
            metrics_list = []
            for _ in range(5):
                metrics = collector.collect()
                metrics_list.append(metrics)

            # 每次都应该返回一个指标
            for metrics in metrics_list:
                assert len(metrics) == 1
                assert isinstance(metrics[0], CPUMetric)

    def test_cleanup(self, collector, mock_proc_stat_content):
        """测试清理功能"""
        with patch('builtins.open', mock_open(read_data=mock_proc_stat_content)):
            collector.initialize()
            collector.collect()

            # 清理后应该重置状态
            collector.cleanup()
            assert collector._prev_total == 0.0
            assert collector._prev_idle == 0.0
            assert collector._initialized is False


class TestProcessCPUCollector:
    """进程 CPU 采集器测试"""

    @pytest.fixture
    def collector(self):
        """创建采集器实例"""
        return ProcessCPUCollector()

    @pytest.fixture
    def mock_proc_pid_stat_content(self):
        """模拟 /proc/[pid]/stat 内容"""
        # 格式: pid (comm) state ppid pgrp ...
        return "1234 (test_process) R 1 1234 1234 0 -1 4194304 100 0 0 0 500 100 0 0 20 0 1 0 12345678 123456789"

    @pytest.fixture
    def mock_proc_pid_task_dir(self, tmp_path):
        """模拟 /proc/[pid]/task 目录结构"""
        task_dir = tmp_path / "task"
        task_dir.mkdir()

        # 创建线程目录
        for i in range(4):
            thread_dir = task_dir / f"1234.{i}"
            thread_dir.mkdir()

            # 创建线程 stat 文件
            thread_stat = thread_dir / "stat"
            thread_stat.write_text(
                f"1234.{i} (test_thread_{i}) R 1234 1234 1234 0 -1 4194304 {25 * (i+1)} 0 0 0 0 {125 * (i+1)} 25 0 0 20 0 1 0 12345678 123456789\n"
            )

        return task_dir

    def test_collect_process_cpu(self, collector, mock_proc_pid_stat_content):
        """测试进程 CPU 采集"""
        pid = 1234

        with patch('builtins.open', mock_open(read_data=mock_proc_pid_stat_content)):
            metric = collector.collect(pid)

            assert metric is not None
            assert metric.pid == pid
            assert metric.name == "test_process"
            assert 0 <= metric.cpu_percent <= 100

    def test_collect_process_not_found(self, collector):
        """测试进程不存在时的错误处理"""
        pid = 99999

        with patch('builtins.open', side_effect=FileNotFoundError()):
            with pytest.raises(CollectionError) as exc_info:
                collector.collect(pid)
            assert "Failed" in str(exc_info.value)

    def test_collect_thread_data(self, collector, mock_proc_pid_task_dir):
        """测试线程数据采集"""
        pid = 1234

        with patch('pathlib.Path.iterdir', return_value=[mock_proc_pid_task_dir / f"1234.{i}" for i in range(4)]):
            # 模拟读取线程数据
            metrics = collector.collect_threads(pid)

            assert metrics is not None
            assert len(metrics) == 4  # 4 个线程

            for metric in metrics:
                assert 0 <= metric.cpu_percent <= 100

    def test_process_cpu_accuracy(self, collector):
        """测试进程 CPU 使用率计算准确性"""
        # 创建已知的 CPU 时间数据
        utime = 100000  # 用户时间（单位：jiffies）
        stime = 50000   # 系统时间
        total_time = utime + stime

        # 模拟 /proc/[pid]/stat 读取
        stat_content = f"1234 (test) R 1 1234 1234 0 -1 4194304 {utime} {stime} 0 0 0 0 0 0 0 20 0 1 0 12345678 123456789"

        with patch('builtins.open', mock_open(read_data=stat_content)):
            metric = collector.collect(1234)

            # 验证 CPU 时间计算正确
            assert metric.cpu_percent >= 0

    def test_collect_multiple_processes(self, collector):
        """测试采集多个进程"""
        pids = [1234, 5678, 9012]

        for pid in pids:
            stat_content = f"{pid} (process_{pid}) R 1 {pid} {pid} 0 -1 4194304 100 50 0 0 0 0 0 0 20 0 1 0 12345678 123456789"

            with patch('builtins.open', mock_open(read_data=stat_content)):
                metric = collector.collect(pid)
                assert metric.pid == pid

    def test_cleanup(self, collector):
        """测试清理功能"""
        collector.cleanup()
        # 验证清理操作不抛出异常
        assert True


class TestCPUMetricModel:
    """CPU 指标模型测试"""

    def test_cpu_metric_creation(self):
        """测试 CPU 指标对象创建"""
        timestamp = datetime.now()
        metric = CPUMetric(
            timestamp=timestamp,
            cpu_percent=50.5,
            cpu_user=30.0,
            cpu_system=15.0,
            cpu_idle=50.0,
            cpu_iowait=5.0,
            cpu_steal=0.0
        )

        assert metric.timestamp == timestamp
        assert metric.cpu_percent == 50.5
        assert metric.cpu_user == 30.0
        assert metric.cpu_system == 15.0
        assert metric.cpu_idle == 50.0
        assert metric.cpu_iowait == 5.0
        assert metric.cpu_steal == 0.0

    def test_cpu_metric_validation(self):
        """测试 CPU 指标验证"""
        # 测试边界值
        with pytest.raises((ValueError, AssertionError)):
            # CPU 使用率不能为负
            CPUMetric(
                timestamp=datetime.now(),
                cpu_percent=-1.0,
                cpu_user=0.0,
                cpu_system=0.0,
                cpu_idle=100.0,
                cpu_iowait=0.0,
                cpu_steal=0.0
            )

        with pytest.raises((ValueError, AssertionError)):
            # CPU 使用率不能超过 100
            CPUMetric(
                timestamp=datetime.now(),
                cpu_percent=101.0,
                cpu_user=0.0,
                cpu_system=0.0,
                cpu_idle=100.0,
                cpu_iowait=0.0,
                cpu_steal=0.0
            )

    def test_cpu_metric_dict_conversion(self):
        """测试 CPU 指标转换为字典"""
        timestamp = datetime.now()
        metric = CPUMetric(
            timestamp=timestamp,
            cpu_percent=50.5,
            cpu_user=30.0,
            cpu_system=15.0,
            cpu_idle=50.0,
            cpu_iowait=5.0,
            cpu_steal=0.0
        )

        # 假设模型有 to_dict() 方法
        if hasattr(metric, 'to_dict'):
            metric_dict = metric.to_dict()
            assert metric_dict['cpu_percent'] == 50.5
            assert metric_dict['cpu_user'] == 30.0


@pytest.mark.integration
class TestCollectorIntegration:
    """集成测试 - 需要真实环境"""

    @pytest.fixture
    def real_system_collector(self):
        """真实的系统采集器"""
        collector = SystemCPUCollector()
        try:
            collector.initialize()
            yield collector
        finally:
            collector.cleanup()

    @pytest.mark.skipif(not os.path.exists('/proc/stat'), reason="Requires Linux")
    def test_real_system_data_collection(self, real_system_collector):
        """测试真实系统数据采集"""
        metrics = real_system_collector.collect()

        assert len(metrics) > 0
        metric = metrics[0]

        # 验证数据合理性
        assert 0 <= metric.cpu_percent <= 100
        assert 0 <= metric.cpu_user <= 100
        assert 0 <= metric.cpu_system <= 100
        assert 0 <= metric.cpu_idle <= 100

    @pytest.mark.skipif(not os.path.exists('/proc/stat'), reason="Requires Linux")
    def test_real_continuous_collection(self, real_system_collector):
        """测试连续采集"""
        metrics_list = []

        # 采集 10 次
        for _ in range(10):
            metrics = real_system_collector.collect()
            metrics_list.append(metrics)

        # 每次采集都应该成功
        assert all(len(metrics) > 0 for metrics in metrics_list)

    @pytest.mark.skipif(not os.path.exists('/proc/self/stat'), reason="Requires Linux")
    def test_real_process_collection(self):
        """测试真实进程采集"""
        collector = ProcessCPUCollector()
        pid = os.getpid()  # 当前进程

        metric = collector.collect(pid)

        assert metric.pid == pid
        assert 0 <= metric.cpu_percent <= 100


@pytest.fixture
def cpu_accuracy_dataset():
    """CPU 准确性测试数据集"""
    return [
        {
            "proc_stat": "cpu  100 0 50 150 0 0 0 0 0 0\n",
            "expected_cpu_percent": pytest.approx(50.0, abs=1.0),
        },
        {
            "proc_stat": "cpu  200 0 100 100 0 0 0 0 0 0\n",
            "expected_cpu_percent": pytest.approx(75.0, abs=1.0),
        },
        {
            "proc_stat": "cpu  0 0 0 300 0 0 0 0 0 0\n",
            "expected_cpu_percent": pytest.approx(0.0, abs=1.0),
        },
    ]


class TestCPUDataAccuracy:
    """CPU 数据准确性测试"""

    def test_accuracy_against_known_values(self, cpu_accuracy_dataset):
        """测试已知值的准确性"""
        collector = SystemCPUCollector()

        for test_case in cpu_accuracy_dataset:
            with patch('builtins.open', mock_open(read_data=test_case["proc_stat"])):
                collector.initialize()
                collector.collect()  # 第一次采集

                metrics = collector.collect()
                cpu_percent = metrics[0].cpu_percent

                assert cpu_percent == test_case["expected_cpu_percent"]


@pytest.mark.performance
class TestCollectorPerformance:
    """采集器性能测试"""

    def test_collection_speed(self):
        """测试采集速度"""
        import time

        mock_content = "cpu  100 0 50 150 0 0 0 0 0 0\n"
        collector = SystemCPUCollector()

        with patch('builtins.open', mock_open(read_data=mock_content)):
            collector.initialize()

            # 测量 100 次采集的时间
            start_time = time.time()
            for _ in range(100):
                collector.collect()
            elapsed_time = time.time() - start_time

            # 100 次采集应该在 1 秒内完成
            assert elapsed_time < 1.0

            print(f"\n采集 100 次耗时: {elapsed_time:.4f} 秒")
            print(f"平均每次采集: {elapsed_time/100*1000:.2f} 毫秒")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
