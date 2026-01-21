#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory 数据采集器单元测试

测试内容:
1. 系统内存数据采集
2. 进程内存数据采集
3. 数据准确性验证
4. 错误处理
"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from aiops.memory.collectors.system_memory import SystemMemoryCollector
from aiops.memory.collectors.process_memory import ProcessMemoryCollector
from aiops.memory.models import MemoryMetric, ProcessMemoryMetric
from aiops.core.exceptions import CollectionError


class TestSystemMemoryCollector:
    """系统内存采集器测试"""

    @pytest.fixture
    def collector(self):
        """创建采集器实例"""
        return SystemMemoryCollector()

    @pytest.fixture
    def mock_meminfo_content(self):
        """模拟 /proc/meminfo 内容"""
        return """MemTotal:       16384000 kB
MemFree:         4096000 kB
MemAvailable:    8192000 kB
Buffers:          512000 kB
Cached:          2048000 kB
SwapCached:        10000 kB
Active:          6144000 kB
Inactive:        2048000 kB
Slab:             256000 kB
SwapTotal:       8192000 kB
SwapFree:        6144000 kB
Dirty:             10000 kB
Writeback:             0 kB
"""

    @pytest.fixture
    def mock_vmstat_content(self):
        """模拟 /proc/vmstat 内容"""
        return """nr_free_pages 1024000
nr_inactive_anon 512000
nr_active_anon 1536000
nr_inactive_file 512000
nr_active_file 1024000
pswpin 1000
pswpout 2000
pgfault 100000
pgmajfault 500
"""

    def test_initialize_success(self, collector, tmp_path):
        """测试成功初始化"""
        # 创建模拟的 /proc/meminfo 文件
        meminfo = tmp_path / "meminfo"
        meminfo.write_text("MemTotal: 16384000 kB\n")

        vmstat = tmp_path / "vmstat"
        vmstat.write_text("nr_free_pages 1024000\n")

        with patch.object(collector, 'PROC_MEMINFO_PATH', str(meminfo)):
            with patch.object(collector, 'PROC_VMSTAT_PATH', str(vmstat)):
                with patch('os.path.exists', return_value=True):
                    collector.initialize()
                    assert collector._initialized is True

    def test_initialize_file_not_found(self, collector):
        """测试文件不存在时的错误处理"""
        with patch.object(collector, 'PROC_MEMINFO_PATH', '/nonexistent/proc/meminfo'):
            with pytest.raises(CollectionError) as exc_info:
                collector.initialize()
            assert "Cannot read" in str(exc_info.value)

    def test_collect_memory_metrics(self, collector, mock_meminfo_content, mock_vmstat_content):
        """测试内存指标采集"""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=[
                mock_open(read_data=mock_meminfo_content).return_value,
                mock_open(read_data=mock_vmstat_content).return_value,
                mock_open(read_data=mock_meminfo_content).return_value,
                mock_open(read_data=mock_vmstat_content).return_value
            ]):
                collector.initialize()
                metrics = collector.collect()

                assert len(metrics) == 1
                metric = metrics[0]
                assert isinstance(metric, MemoryMetric)
                assert hasattr(metric, 'mem_total')
                assert hasattr(metric, 'mem_free')
                assert hasattr(metric, 'mem_available')
                assert hasattr(metric, 'mem_used')
                assert hasattr(metric, 'swap_total')
                assert hasattr(metric, 'swap_free')

    def test_memory_percent_calculation(self, collector, mock_meminfo_content, mock_vmstat_content):
        """测试内存使用率计算准确性"""
        with patch('builtins.open', side_effect=[
            mock_open(read_data=mock_meminfo_content).return_value,
            mock_open(read_data=mock_vmstat_content).return_value
        ]):
            collector.initialize()
            metrics = collector.collect()
            metric = metrics[0]

            # 内存使用率应该在合理范围内
            assert 0 <= metric.mem_used_percent <= 100
            assert 0 <= metric.mem_available_percent <= 100
            assert 0 <= metric.swap_used_percent <= 100

    def test_memory_values_consistency(self, collector, mock_meminfo_content, mock_vmstat_content):
        """测试内存值的一致性"""
        with patch('builtins.open', side_effect=[
            mock_open(read_data=mock_meminfo_content).return_value,
            mock_open(read_data=mock_vmstat_content).return_value
        ]):
            collector.initialize()
            metrics = collector.collect()
            metric = metrics[0]

            # mem_used + mem_available 应该接近 mem_total
            total_check = metric.mem_used + metric.mem_available
            assert abs(total_check - metric.mem_total) / metric.mem_total < 0.1  # 允许 10% 误差

            # swap_used + swap_free 应该等于 swap_total
            swap_check = metric.swap_used + metric.swap_free
            assert abs(swap_check - metric.swap_total) / metric.swap_total < 0.01  # 允许 1% 误差

    def test_collect_parse_error(self, collector):
        """测试解析错误处理"""
        invalid_content = "MemTotal: invalid data\n"

        with patch('builtins.open', mock_open(read_data=invalid_content)):
            collector.initialize()
            with pytest.raises(CollectionError) as exc_info:
                collector.collect()
            assert "Failed to parse" in str(exc_info.value)

    def test_multiple_collections(self, collector, mock_meminfo_content, mock_vmstat_content):
        """测试多次采集的一致性"""
        with patch('builtins.open', side_effect=[
            mock_open(read_data=mock_meminfo_content).return_value,
            mock_open(read_data=mock_vmstat_content).return_value
        ] * 5):
            collector.initialize()

            # 多次采集
            metrics_list = []
            for _ in range(5):
                metrics = collector.collect()
                metrics_list.append(metrics)

            # 每次都应该返回一个指标
            for metrics in metrics_list:
                assert len(metrics) == 1
                assert isinstance(metrics[0], MemoryMetric)

    def test_cleanup(self, collector, mock_meminfo_content, mock_vmstat_content):
        """测试清理功能"""
        with patch('builtins.open', side_effect=[
            mock_open(read_data=mock_meminfo_content).return_value,
            mock_open(read_data=mock_vmstat_content).return_value
        ]):
            collector.initialize()
            collector.collect()

            # 清理后应该重置状态
            collector.cleanup()
            assert collector._initialized is False


class TestProcessMemoryCollector:
    """进程内存采集器测试"""

    @pytest.fixture
    def collector(self):
        """创建采集器实例"""
        return ProcessMemoryCollector(max_processes=10)

    @pytest.fixture
    def mock_proc_status_content(self):
        """模拟 /proc/[pid]/status 内容"""
        return """Name:	test_process
State:	R (running)
Pid:	1234
PPid:	1
VmSize:	  102400 kB
VmRSS:	   51200 kB
VmData:	   20480 kB
VmStk:	     136 kB
VmExe:	    4096 kB
VmLib:	    8192 kB
VmSwap:	    2048 kB
Threads:	4
"""

    def test_collect_process_memory(self, collector, mock_proc_status_content):
        """测试进程内存采集"""
        pid = 1234

        with patch('builtins.open', mock_open(read_data=mock_proc_status_content)):
            with patch('psutil.Process') as mock_process:
                mock_proc = Mock()
                mock_proc.pid = pid
                mock_proc.name.return_value = "test_process"
                mock_proc.username.return_value = "testuser"
                mock_proc.status.return_value = "running"
                mock_process.return_value = mock_proc

                collector.initialize()
                metrics = collector.collect(pid=pid)

                assert len(metrics) > 0
                metric = metrics[0]
                assert isinstance(metric, ProcessMemoryMetric)
                assert metric.pid == pid
                assert metric.name == "test_process"

    def test_collect_top_processes(self, collector):
        """测试采集 top N 进程"""
        with patch('psutil.process_iter') as mock_iter:
            # 模拟 20 个进程
            mock_processes = []
            for i in range(20):
                mock_proc = Mock()
                mock_proc.pid = 1000 + i
                mock_proc.name.return_value = f"process_{i}"
                mock_proc.username.return_value = "testuser"
                mock_proc.status.return_value = "running"
                mock_proc.memory_info.return_value = Mock(
                    rss=1024 * 1024 * (20 - i),  # 递减的内存使用
                    vms=2048 * 1024 * (20 - i)
                )
                mock_processes.append(mock_proc)

            mock_iter.return_value = mock_processes

            collector.initialize()
            metrics = collector.collect()

            # 应该返回 top 10 个进程
            assert len(metrics) <= 10
            # 应该按内存使用量排序
            for i in range(len(metrics) - 1):
                assert metrics[i].vm_rss >= metrics[i + 1].vm_rss

    def test_collect_process_not_found(self, collector):
        """测试进程不存在时的错误处理"""
        pid = 99999

        with patch('psutil.Process', side_effect=psutil.NoSuchProcess(pid)):
            collector.initialize()
            metrics = collector.collect(pid=pid)
            # 应该返回空列表而不是抛出异常
            assert len(metrics) == 0

    def test_memory_unit_conversion(self, collector, mock_proc_status_content):
        """测试内存单位转换"""
        pid = 1234

        with patch('builtins.open', mock_open(read_data=mock_proc_status_content)):
            with patch('psutil.Process') as mock_process:
                mock_proc = Mock()
                mock_proc.pid = pid
                mock_proc.name.return_value = "test_process"
                mock_proc.username.return_value = "testuser"
                mock_proc.status.return_value = "running"
                mock_process.return_value = mock_proc

                collector.initialize()
                metrics = collector.collect(pid=pid)
                metric = metrics[0]

                # 验证 MB 转换
                assert metric.rss_mb == metric.vm_rss / (1024 * 1024)
                assert metric.vms_mb == metric.vm_size / (1024 * 1024)
                assert metric.swap_mb == metric.vm_swap / (1024 * 1024)

    def test_cleanup(self, collector):
        """测试清理功能"""
        collector.initialize()
        collector.cleanup()
        assert collector._initialized is False


class TestMemoryMetricModel:
    """内存指标模型测试"""

    def test_memory_metric_creation(self):
        """测试内存指标对象创建"""
        timestamp = datetime.now()
        metric = MemoryMetric(
            timestamp=timestamp,
            mem_total=16 * 1024**3,
            mem_free=4 * 1024**3,
            mem_available=8 * 1024**3,
            mem_used=8 * 1024**3,
            buffers=512 * 1024**2,
            cached=2 * 1024**3,
            slab=256 * 1024**2,
            swap_total=8 * 1024**3,
            swap_free=6 * 1024**3,
            swap_used=2 * 1024**3,
            swap_cached=10 * 1024**2
        )

        assert metric.timestamp == timestamp
        assert metric.mem_total == 16 * 1024**3
        assert metric.mem_free == 4 * 1024**3
        assert metric.mem_available == 8 * 1024**3

    def test_memory_metric_properties(self):
        """测试内存指标属性计算"""
        metric = MemoryMetric(
            timestamp=datetime.now(),
            mem_total=16 * 1024**3,
            mem_free=4 * 1024**3,
            mem_available=8 * 1024**3,
            mem_used=8 * 1024**3,
            buffers=512 * 1024**2,
            cached=2 * 1024**3,
            slab=256 * 1024**2,
            swap_total=8 * 1024**3,
            swap_free=6 * 1024**3,
            swap_used=2 * 1024**3,
            swap_cached=10 * 1024**2
        )

        # 测试百分比计算
        assert metric.mem_used_percent == pytest.approx(50.0, abs=0.1)
        assert metric.mem_available_percent == pytest.approx(50.0, abs=0.1)
        assert metric.swap_used_percent == pytest.approx(25.0, abs=0.1)

    def test_process_memory_metric_creation(self):
        """测试进程内存指标对象创建"""
        timestamp = datetime.now()
        metric = ProcessMemoryMetric(
            timestamp=timestamp,
            pid=1234,
            name="test_process",
            vm_size=100 * 1024**2,
            vm_rss=50 * 1024**2,
            vm_data=20 * 1024**2,
            vm_stk=136 * 1024,
            vm_exe=4 * 1024**2,
            vm_lib=8 * 1024**2,
            vm_swap=2 * 1024**2,
            username="testuser",
            status="R"  # Use single-letter status code
        )

        assert metric.pid == 1234
        assert metric.name == "test_process"
        assert metric.rss_mb == pytest.approx(50.0, abs=0.1)
        assert metric.vms_mb == pytest.approx(100.0, abs=0.1)


@pytest.mark.integration
class TestMemoryCollectorIntegration:
    """集成测试 - 需要真实环境"""

    @pytest.fixture
    def real_system_collector(self):
        """真实的系统采集器"""
        collector = SystemMemoryCollector()
        try:
            collector.initialize()
            yield collector
        finally:
            collector.cleanup()

    @pytest.mark.skipif(not os.path.exists('/proc/meminfo'), reason="Requires Linux")
    def test_real_system_data_collection(self, real_system_collector):
        """测试真实系统数据采集"""
        metrics = real_system_collector.collect()

        assert len(metrics) > 0
        metric = metrics[0]

        # 验证数据合理性
        assert 0 <= metric.mem_used_percent <= 100
        assert 0 <= metric.mem_available_percent <= 100
        assert metric.mem_total > 0
        assert metric.mem_available > 0

    @pytest.mark.skipif(not os.path.exists('/proc/meminfo'), reason="Requires Linux")
    def test_real_continuous_collection(self, real_system_collector):
        """测试连续采集"""
        metrics_list = []

        # 采集 10 次
        for _ in range(10):
            metrics = real_system_collector.collect()
            metrics_list.append(metrics)

        # 每次采集都应该成功
        assert all(len(metrics) > 0 for metrics in metrics_list)

    @pytest.mark.skipif(not os.path.exists('/proc/self/status'), reason="Requires Linux")
    def test_real_process_collection(self):
        """测试真实进程采集"""
        collector = ProcessMemoryCollector()
        collector.initialize()
        pid = os.getpid()  # 当前进程

        metrics = collector.collect(pid=pid)

        assert len(metrics) > 0
        metric = metrics[0]
        assert metric.pid == pid
        assert metric.vm_rss > 0


@pytest.mark.performance
class TestMemoryCollectorPerformance:
    """采集器性能测试"""

    def test_collection_speed(self):
        """测试采集速度"""
        import time

        mock_meminfo = "MemTotal: 16384000 kB\nMemFree: 4096000 kB\nMemAvailable: 8192000 kB\n"
        mock_vmstat = "pswpin 1000\npswpout 2000\n"
        collector = SystemMemoryCollector()

        with patch('builtins.open', side_effect=[
            mock_open(read_data=mock_meminfo).return_value,
            mock_open(read_data=mock_vmstat).return_value
        ] * 100):
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
