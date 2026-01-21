#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory 异常检测器单元测试

测试内容:
1. 内存泄漏检测
2. OOM 风险检测
3. Swap 异常检测
"""

import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from aiops.memory.detectors import MemoryLeakDetector, OOMRiskDetector, SwapAnomalyDetector
from aiops.memory.models import MemoryMetric, ProcessMemoryMetric
from aiops.cpu.models import AnomalyEvent


class TestMemoryLeakDetector:
    """内存泄漏检测器测试"""

    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        return MemoryLeakDetector(
            min_samples=10,
            growth_threshold_mb=10.0,
            confidence_threshold=0.7
        )

    @pytest.fixture
    def leak_metrics(self):
        """生成内存泄漏场景的指标"""
        metrics = []
        start_time = datetime.now()
        base_rss = 100  # MB

        for i in range(100):
            # 模拟线性增长的内存泄漏
            rss_mb = base_rss + (i * 0.5)  # 每秒增长 0.5 MB = 1800 MB/hour

            metric = ProcessMemoryMetric(
                timestamp=start_time + timedelta(seconds=i),
                pid=1234,
                name="leaky_process",
                vm_size=int(rss_mb * 1.5 * 1024 * 1024),
                vm_rss=int(rss_mb * 1024 * 1024),
                vm_data=int(rss_mb * 0.8 * 1024 * 1024),
                vm_stk=136 * 1024,
                vm_exe=4 * 1024 * 1024,
                vm_lib=8 * 1024 * 1024,
                vm_swap=0,
                username="testuser",
                status="R"
            )
            metrics.append(metric)

        return metrics

    @pytest.fixture
    def stable_metrics(self):
        """生成稳定内存使用的指标"""
        metrics = []
        start_time = datetime.now()
        base_rss = 100  # MB

        for i in range(100):
            # 稳定的内存使用，有小幅波动
            import random
            rss_mb = base_rss + random.uniform(-2, 2)

            metric = ProcessMemoryMetric(
                timestamp=start_time + timedelta(seconds=i),
                pid=1234,
                name="stable_process",
                vm_size=int(rss_mb * 1.5 * 1024 * 1024),
                vm_rss=int(rss_mb * 1024 * 1024),
                vm_data=int(rss_mb * 0.8 * 1024 * 1024),
                vm_stk=136 * 1024,
                vm_exe=4 * 1024 * 1024,
                vm_lib=8 * 1024 * 1024,
                vm_swap=0,
                username="testuser",
                status="R"
            )
            metrics.append(metric)

        return metrics

    def test_detect_memory_leak(self, detector, leak_metrics):
        """测试检测内存泄漏"""
        anomalies = detector.detect(leak_metrics)

        assert len(anomalies) > 0
        anomaly = anomalies[0]
        assert isinstance(anomaly, AnomalyEvent)
        assert anomaly.type == "memory_leak"
        assert anomaly.metrics["growth_rate_mb_hour"] > 10.0
        assert anomaly.confidence > 0.7

    def test_no_leak_detected(self, detector, stable_metrics):
        """测试稳定内存不被误报为泄漏"""
        anomalies = detector.detect(stable_metrics)

        assert len(anomalies) == 0

    def test_insufficient_samples(self, detector):
        """测试样本不足时的处理"""
        metrics = []
        start_time = datetime.now()

        for i in range(5):  # 少于 min_samples
            metric = ProcessMemoryMetric(
                timestamp=start_time + timedelta(seconds=i),
                pid=1234,
                name="test_process",
                vm_size=100 * 1024 * 1024,
                vm_rss=50 * 1024 * 1024,
                vm_data=20 * 1024 * 1024,
                vm_stk=136 * 1024,
                vm_exe=4 * 1024 * 1024,
                vm_lib=8 * 1024 * 1024,
                vm_swap=0,
                username="testuser",
                status="R"
            )
            metrics.append(metric)

        anomalies = detector.detect(metrics)
        assert len(anomalies) == 0

    def test_multiple_processes(self, detector):
        """测试多进程场景"""
        metrics = []
        start_time = datetime.now()

        # 进程 1: 有泄漏
        for i in range(50):
            rss_mb = 100 + (i * 0.5)
            metric = ProcessMemoryMetric(
                timestamp=start_time + timedelta(seconds=i),
                pid=1234,
                name="leaky_process",
                vm_size=int(rss_mb * 1.5 * 1024 * 1024),
                vm_rss=int(rss_mb * 1024 * 1024),
                vm_data=int(rss_mb * 0.8 * 1024 * 1024),
                vm_stk=136 * 1024,
                vm_exe=4 * 1024 * 1024,
                vm_lib=8 * 1024 * 1024,
                vm_swap=0,
                username="testuser",
                status="R"
            )
            metrics.append(metric)

        # 进程 2: 稳定
        for i in range(50):
            metric = ProcessMemoryMetric(
                timestamp=start_time + timedelta(seconds=i),
                pid=5678,
                name="stable_process",
                vm_size=100 * 1024 * 1024,
                vm_rss=50 * 1024 * 1024,
                vm_data=20 * 1024 * 1024,
                vm_stk=136 * 1024,
                vm_exe=4 * 1024 * 1024,
                vm_lib=8 * 1024 * 1024,
                vm_swap=0,
                username="testuser",
                status="R"
            )
            metrics.append(metric)

        anomalies = detector.detect(metrics)

        # 应该只检测到进程 1 的泄漏
        assert len(anomalies) == 1
        assert anomalies[0].metrics["pid"] == 1234


class TestOOMRiskDetector:
    """OOM 风险检测器测试"""

    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        return OOMRiskDetector(
            prediction_window_hours=24,
            risk_threshold_percent=90.0,
            min_samples=10
        )

    @pytest.fixture
    def oom_risk_metrics(self):
        """生成 OOM 风险场景的指标"""
        metrics = []
        start_time = datetime.now()
        total_memory = 16 * 1024 ** 3  # 16 GB

        for i in range(100):
            # 模拟内存使用率从 70% 线性增长到 95%
            usage_percent = 70 + (i * 0.25)
            used_memory = int(total_memory * usage_percent / 100)

            metric = MemoryMetric(
                timestamp=start_time + timedelta(seconds=i),
                mem_total=total_memory,
                mem_free=total_memory - used_memory,
                mem_available=total_memory - used_memory,
                mem_used=used_memory,
                buffers=512 * 1024 ** 2,
                cached=2 * 1024 ** 3,
                slab=256 * 1024 ** 2,
                swap_total=8 * 1024 ** 3,
                swap_free=6 * 1024 ** 3,
                swap_used=2 * 1024 ** 3,
                swap_cached=10 * 1024 ** 2
            )
            metrics.append(metric)

        return metrics

    @pytest.fixture
    def stable_memory_metrics(self):
        """生成稳定内存使用的指标"""
        metrics = []
        start_time = datetime.now()
        total_memory = 16 * 1024 ** 3

        for i in range(100):
            # 稳定在 60% 左右
            usage_percent = 60
            used_memory = int(total_memory * usage_percent / 100)

            metric = MemoryMetric(
                timestamp=start_time + timedelta(seconds=i),
                mem_total=total_memory,
                mem_free=total_memory - used_memory,
                mem_available=total_memory - used_memory,
                mem_used=used_memory,
                buffers=512 * 1024 ** 2,
                cached=2 * 1024 ** 3,
                slab=256 * 1024 ** 2,
                swap_total=8 * 1024 ** 3,
                swap_free=6 * 1024 ** 3,
                swap_used=2 * 1024 ** 3,
                swap_cached=10 * 1024 ** 2
            )
            metrics.append(metric)

        return metrics

    def test_detect_oom_risk(self, detector, oom_risk_metrics):
        """测试检测 OOM 风险"""
        anomalies = detector.detect(oom_risk_metrics)

        assert len(anomalies) > 0
        anomaly = anomalies[0]
        assert isinstance(anomaly, AnomalyEvent)
        assert anomaly.type == "oom_risk"
        assert anomaly.metrics["predicted_usage_percent"] >= 90.0
        assert "time_to_oom_hours" in anomaly.metrics

    def test_no_oom_risk(self, detector, stable_memory_metrics):
        """测试稳定内存不被误报为 OOM 风险"""
        anomalies = detector.detect(stable_memory_metrics)

        assert len(anomalies) == 0

    def test_insufficient_samples(self, detector):
        """测试样本不足时的处理"""
        metrics = []
        start_time = datetime.now()
        total_memory = 16 * 1024 ** 3

        for i in range(5):  # 少于 min_samples
            metric = MemoryMetric(
                timestamp=start_time + timedelta(seconds=i),
                mem_total=total_memory,
                mem_free=total_memory // 2,
                mem_available=total_memory // 2,
                mem_used=total_memory // 2,
                buffers=512 * 1024 ** 2,
                cached=2 * 1024 ** 3,
                slab=256 * 1024 ** 2,
                swap_total=8 * 1024 ** 3,
                swap_free=6 * 1024 ** 3,
                swap_used=2 * 1024 ** 3,
                swap_cached=10 * 1024 ** 2
            )
            metrics.append(metric)

        anomalies = detector.detect(metrics)
        assert len(anomalies) == 0


class TestSwapAnomalyDetector:
    """Swap 异常检测器测试"""

    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        return SwapAnomalyDetector(
            threshold_percent=10.0,
            spike_multiplier=2.0,
            min_samples=10
        )

    @pytest.fixture
    def high_swap_metrics(self):
        """生成持续高 swap 使用的指标"""
        metrics = []
        start_time = datetime.now()
        total_swap = 8 * 1024 ** 3

        for i in range(50):
            # 持续高 swap 使用 (20%)
            swap_used = int(total_swap * 0.20)

            metric = MemoryMetric(
                timestamp=start_time + timedelta(seconds=i),
                mem_total=16 * 1024 ** 3,
                mem_free=4 * 1024 ** 3,
                mem_available=8 * 1024 ** 3,
                mem_used=8 * 1024 ** 3,
                buffers=512 * 1024 ** 2,
                cached=2 * 1024 ** 3,
                slab=256 * 1024 ** 2,
                swap_total=total_swap,
                swap_free=total_swap - swap_used,
                swap_used=swap_used,
                swap_cached=10 * 1024 ** 2
            )
            metrics.append(metric)

        return metrics

    @pytest.fixture
    def swap_spike_metrics(self):
        """生成 swap 突增的指标"""
        metrics = []
        start_time = datetime.now()
        total_swap = 8 * 1024 ** 3

        for i in range(50):
            # 前半部分低 swap，后半部分突增
            if i < 25:
                swap_used = int(total_swap * 0.02)  # 2%
            else:
                swap_used = int(total_swap * 0.30)  # 30%

            metric = MemoryMetric(
                timestamp=start_time + timedelta(seconds=i),
                mem_total=16 * 1024 ** 3,
                mem_free=4 * 1024 ** 3,
                mem_available=8 * 1024 ** 3,
                mem_used=8 * 1024 ** 3,
                buffers=512 * 1024 ** 2,
                cached=2 * 1024 ** 3,
                slab=256 * 1024 ** 2,
                swap_total=total_swap,
                swap_free=total_swap - swap_used,
                swap_used=swap_used,
                swap_cached=10 * 1024 ** 2
            )
            metrics.append(metric)

        return metrics

    def test_detect_sustained_high_swap(self, detector, high_swap_metrics):
        """测试检测持续高 swap 使用"""
        anomalies = detector.detect(high_swap_metrics)

        # 应该检测到持续高使用
        sustained_anomalies = [a for a in anomalies if a.type == "swap_sustained_high_usage"]
        assert len(sustained_anomalies) > 0

    def test_detect_swap_spike(self, detector, swap_spike_metrics):
        """测试检测 swap 突增"""
        anomalies = detector.detect(swap_spike_metrics)

        # 应该检测到突增
        spike_anomalies = [a for a in anomalies if a.type == "swap_spike"]
        assert len(spike_anomalies) > 0

    def test_no_swap_anomaly(self, detector):
        """测试正常 swap 使用不被误报"""
        metrics = []
        start_time = datetime.now()
        total_swap = 8 * 1024 ** 3

        for i in range(50):
            # 低 swap 使用 (2%)
            swap_used = int(total_swap * 0.02)

            metric = MemoryMetric(
                timestamp=start_time + timedelta(seconds=i),
                mem_total=16 * 1024 ** 3,
                mem_free=4 * 1024 ** 3,
                mem_available=8 * 1024 ** 3,
                mem_used=8 * 1024 ** 3,
                buffers=512 * 1024 ** 2,
                cached=2 * 1024 ** 3,
                slab=256 * 1024 ** 2,
                swap_total=total_swap,
                swap_free=total_swap - swap_used,
                swap_used=swap_used,
                swap_cached=10 * 1024 ** 2
            )
            metrics.append(metric)

        anomalies = detector.detect(metrics)
        assert len(anomalies) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
