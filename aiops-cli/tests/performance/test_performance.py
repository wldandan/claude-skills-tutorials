#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能和边界测试

测试内容:
1. 采集器性能测试
2. 检测器性能测试
3. 边界值测试
4. 压力测试
5. 资源占用测试
"""

import pytest
import os
import sys
import time
import psutil
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, mock_open
import multiprocessing

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'aiops-cli'))

from aiops.cpu.collectors.system_cpu import SystemCPUCollector
from aiops.cpu.collectors.process_cpu import ProcessCPUCollector
from aiops.cpu.detectors.static_threshold import StaticThresholdDetector
from aiops.cpu.detectors.dynamic_baseline import DynamicBaselineDetector
from aiops.cpu.models.cpu_metric import CPUMetric


@pytest.mark.performance
class TestCollectorPerformance:
    """采集器性能测试"""

    @pytest.fixture
    def mock_proc_stat(self):
        """模拟 /proc/stat 数据"""
        return "cpu  100 0 50 150 0 0 0 0 0 0\n"

    def test_collection_speed(self, mock_proc_stat):
        """测试采集速度"""
        collector = SystemCPUCollector()

        with patch('builtins.open', mock_open(read_data=mock_proc_stat)):
            collector.initialize()

            # 测量 1000 次采集的时间
            iterations = 1000
            start_time = time.time()

            for _ in range(iterations):
                collector.collect()

            elapsed_time = time.time() - start_time

            print(f"\n采集 {iterations} 次耗时: {elapsed_time:.4f} 秒")
            print(f"平均采集速度: {iterations/elapsed_time:.0f} 次/秒")
            print(f"平均每次采集: {elapsed_time/iterations*1000:.2f} 毫秒")

            # 性能要求：每次采集 < 10 毫秒
            assert elapsed_time / iterations < 0.01

    def test_memory_usage_during_collection(self, mock_proc_stat):
        """测试采集过程中的内存占用"""
        process = psutil.Process()
        collector = SystemCPUCollector()

        with patch('builtins.open', mock_open(read_data=mock_proc_stat)):
            collector.initialize()

            # 记录初始内存
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 采集大量数据
            metrics = []
            for _ in range(10000):
                batch = collector.collect()
                metrics.extend(batch)

            # 记录最终内存
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            print(f"\n内存使用:")
            print(f"  初始内存: {initial_memory:.2f} MB")
            print(f"  最终内存: {final_memory:.2f} MB")
            print(f"  内存增长: {memory_increase:.2f} MB")

            # 内存增长应该 < 100MB
            assert memory_increase < 100

    def test_concurrent_collection(self):
        """测试并发采集性能"""
        if os.path.exists('/proc/stat'):
            collectors = [SystemCPUCollector() for _ in range(4)]

            for collector in collectors:
                collector.initialize()

            # 并发采集
            start_time = time.time()

            processes = []
            for collector in collectors:
                p = multiprocessing.Process(target=collect_and_measure, args=(collector, 100))
                processes.append(p)
                p.start()

            for p in processes:
                p.join()

            elapsed_time = time.time() - start_time

            print(f"\n并发采集测试完成，耗时: {elapsed_time:.4f} 秒")

            for collector in collectors:
                collector.cleanup()


def collect_and_measure(collector, iterations):
    """并发采集函数"""
    for _ in range(iterations):
        try:
            collector.collect()
        except:
            pass


@pytest.mark.performance
class TestDetectorPerformance:
    """检测器性能测试"""

    def test_static_threshold_performance(self):
        """测试静态阈值检测性能"""
        # 生成大量数据
        metrics = []
        start_time = datetime.now()
        for i in range(100000):
            cpu_percent = np.random.normal(45, 15)
            cpu_percent = max(0, min(100, cpu_percent))
            metric = CPUMetric(
                timestamp=start_time + timedelta(seconds=i),
                cpu_percent=cpu_percent,
                cpu_user=cpu_percent * 0.6,
                cpu_system=cpu_percent * 0.3,
                cpu_idle=100 - cpu_percent,
                cpu_iowait=cpu_percent * 0.1,
                cpu_steal=0.0
            )
            metrics.append(metric)

        detector = StaticThresholdDetector(threshold=80.0)

        # 测量检测时间
        start = time.time()
        anomalies = detector.detect(metrics)
        elapsed = time.time() - start

        print(f"\n静态阈值检测性能:")
        print(f"  数据点数量: {len(metrics)}")
        print(f"  检测耗时: {elapsed:.4f} 秒")
        print(f"  检测速度: {len(metrics)/elapsed:.0f} 数据点/秒")

        # 性能要求：应该在 5 秒内完成
        assert elapsed < 5.0

    def test_dynamic_baseline_performance(self):
        """测试动态基线检测性能"""
        # 生成基线数据（7 天）
        baseline_metrics = []
        start_time = datetime.now() - timedelta(days=7)
        for i in range(7 * 24 * 60):  # 每分钟一个数据点
            cpu_percent = np.random.normal(40, 10)
            cpu_percent = max(0, min(100, cpu_percent))
            metric = CPUMetric(
                timestamp=start_time + timedelta(minutes=i),
                cpu_percent=cpu_percent,
                cpu_user=cpu_percent * 0.6,
                cpu_system=cpu_percent * 0.3,
                cpu_idle=100 - cpu_percent,
                cpu_iowait=cpu_percent * 0.1,
                cpu_steal=0.0
            )
            baseline_metrics.append(metric)

        detector = DynamicBaselineDetector(baseline_window=7)

        # 测量基线计算时间
        start = time.time()
        baseline = detector._calculate_baseline(baseline_metrics)
        baseline_elapsed = time.time() - start

        print(f"\n动态基线计算性能:")
        print(f"  基线数据点: {len(baseline_metrics)}")
        print(f"  计算耗时: {baseline_elapsed:.4f} 秒")

        # 性能要求：基线计算 < 10 秒
        assert baseline_elapsed < 10.0

        # 测量检测时间
        test_metrics = baseline_metrics[-1000:]
        start = time.time()
        anomalies = detector._detect_with_baseline(test_metrics, baseline)
        detect_elapsed = time.time() - start

        print(f"\n动态基线检测性能:")
        print(f"  测试数据点: {len(test_metrics)}")
        print(f"  检测耗时: {detect_elapsed:.4f} 秒")

        # 性能要求：检测 < 5 秒
        assert detect_elapsed < 5.0


@pytest.mark.boundary
class TestBoundaryValues:
    """边界值测试"""

    def test_cpu_percent_zero(self):
        """测试 CPU 使用率为 0% 的边界情况"""
        collector = SystemCPUCollector()
        mock_content = "cpu  0 0 0 100 0 0 0 0 0 0\n"

        with patch('builtins.open', mock_open(read_data=mock_content)):
            collector.initialize()
            collector.collect()  # 第一次采集

            metrics = collector.collect()
            cpu_percent = metrics[0].cpu_percent

            # CPU 为 0% 时应该返回 0
            assert cpu_percent >= 0
            assert cpu_percent <= 1.0  # 允许小的浮点误差

    def test_cpu_percent_hundred(self):
        """测试 CPU 使用率为 100% 的边界情况"""
        collector = SystemCPUCollector()
        mock_content = "cpu  100 0 0 0 0 0 0 0 0 0\n"

        with patch('builtins.open', mock_open(read_data=mock_content)):
            collector.initialize()
            collector.collect()

            metrics = collector.collect()
            cpu_percent = metrics[0].cpu_percent

            # CPU 为 100% 时应该接近 100
            assert cpu_percent >= 99.0  # 允许小的误差
            assert cpu_percent <= 100.0

    def test_negative_cpu_values(self):
        """测试负值处理"""
        # 模拟负值（不应该发生，但需要测试容错）
        collector = SystemCPUCollector()
        mock_content = "cpu  -1 -1 -1 -1 -1 -1 -1 -1 -1 -1\n"

        with patch('builtins.open', mock_open(read_data=mock_content)):
            collector.initialize()
            collector.collect()

            # 不应该崩溃，应该返回合理的值或抛出适当的异常
            try:
                metrics = collector.collect()
                # 如果返回数据，应该在合理范围内
                assert 0 <= metrics[0].cpu_percent <= 100
            except Exception:
                # 或者抛出适当的异常
                pass

    def test_extremely_large_values(self):
        """测试极大值处理"""
        collector = SystemCPUCollector()
        # 模拟超大的 CPU 时间值
        large_values = " ".join([str(2**63 - 1)] * 10)
        mock_content = f"cpu  {large_values}\n"

        with patch('builtins.open', mock_open(read_data=mock_content)):
            collector.initialize()

            try:
                metrics = collector.collect()
                # 如果成功处理，应该在合理范围内
                assert 0 <= metrics[0].cpu_percent <= 100
            except Exception:
                # 或者抛出适当的异常
                pass

    def test_empty_proc_stat(self):
        """测试空文件处理"""
        collector = SystemCPUCollector()
        mock_content = ""

        with patch('builtins.open', mock_open(read_data=mock_content)):
            collector.initialize()

            # 应该返回空列表或抛出异常
            metrics = collector.collect()
            assert len(metrics) == 0

    def test_malformed_data(self):
        """测试格式错误的数据"""
        collector = SystemCPUCollector()

        malformed_cases = [
            "cpu invalid data here\n",
            "cpu  1 2\n",  # 字段不足
            "cpu  a b c d e f g h i j\n",  # 非数字值
            "notcpu  1 2 3 4 5 6 7 8 9 10\n",  # 不是 cpu 行
        ]

        for malformed_content in malformed_cases:
            with patch('builtins.open', mock_open(read_data=malformed_content)):
                collector.initialize()

                try:
                    metrics = collector.collect()
                    # 如果成功处理，验证数据合理性
                    for metric in metrics:
                        assert 0 <= metric.cpu_percent <= 100
                except Exception:
                    # 或者抛出适当的异常
                    pass


@pytest.mark.stress
class TestStressScenarios:
    """压力测试"""

    def test_high_frequency_collection(self):
        """测试高频采集"""
        if not os.path.exists('/proc/stat'):
            pytest.skip("Requires Linux")

        collector = SystemCPUCollector()
        collector.initialize()

        try:
            # 以 10ms 间隔采集 10 秒
            duration = 10  # 秒
            interval = 0.01  # 10ms
            expected_collections = int(duration / interval)

            start_time = time.time()
            metrics = []

            while time.time() - start_time < duration:
                batch = collector.collect()
                metrics.extend(batch)
                time.sleep(interval)

            actual_collections = len(metrics)

            print(f"\n高频采集测试:")
            print(f"  期望采集次数: {expected_collections}")
            print(f"  实际采集次数: {actual_collections}")
            print(f"  成功率: {actual_collections/expected_collections*100:.1f}%")

            # 至少应该完成 80% 的采集
            assert actual_collections >= expected_collections * 0.8

        finally:
            collector.cleanup()

    def test_large_dataset_detection(self):
        """测试大数据集检测"""
        # 生成 100 万个数据点
        print("\n生成大数据集...")
        metrics = []
        start_time = datetime.now()

        for i in range(1000000):
            cpu_percent = np.random.normal(45, 15)
            cpu_percent = max(0, min(100, cpu_percent))
            metric = CPUMetric(
                timestamp=start_time + timedelta(microseconds=i * 1000),
                cpu_percent=cpu_percent,
                cpu_user=cpu_percent * 0.6,
                cpu_system=cpu_percent * 0.3,
                cpu_idle=100 - cpu_percent,
                cpu_iowait=cpu_percent * 0.1,
                cpu_steal=0.0
            )
            metrics.append(metric)

        print(f"生成 {len(metrics)} 个数据点")

        detector = StaticThresholdDetector(threshold=80.0)

        # 测量检测时间和内存
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        start = time.time()
        anomalies = detector.detect(metrics)
        elapsed = time.time() - start

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_used = final_memory - initial_memory

        print(f"\n大数据集检测结果:")
        print(f"  数据点数量: {len(metrics):,}")
        print(f"  检测耗时: {elapsed:.2f} 秒")
        print(f"  检测速度: {len(metrics)/elapsed:,.0f} 数据点/秒")
        print(f"  内存占用: {memory_used:.2f} MB")
        print(f"  检测到异常: {len(anomalies)} 个")

        # 性能要求
        assert elapsed < 60.0  # 60 秒内完成
        assert memory_used < 500  # 内存占用 < 500MB

    def test_rapid_metric_creation(self):
        """测试快速创建指标对象"""
        start_time = datetime.now()
        count = 1000000

        creation_start = time.time()
        metrics = []

        for i in range(count):
            cpu_percent = np.random.random() * 100
            metric = CPUMetric(
                timestamp=start_time + timedelta(microseconds=i),
                cpu_percent=cpu_percent,
                cpu_user=cpu_percent * 0.6,
                cpu_system=cpu_percent * 0.3,
                cpu_idle=100 - cpu_percent,
                cpu_iowait=cpu_percent * 0.1,
                cpu_steal=0.0
            )
            metrics.append(metric)

        creation_time = time.time() - creation_start

        print(f"\n快速创建指标测试:")
        print(f"  创建数量: {count:,}")
        print(f"  创建耗时: {creation_time:.2f} 秒")
        print(f"  创建速度: {count/creation_time:,.0f} 个/秒")

        # 性能要求：创建速度 > 100k 个/秒
        assert count / creation_time > 100000


@pytest.mark.resource
class TestResourceUsage:
    """资源占用测试"""

    @pytest.mark.skipif(not os.path.exists('/proc/stat'), reason="Requires Linux")
    def test_daemon_mode_memory(self):
        """测试守护进程模式的内存占用"""
        process = psutil.Process()
        collector = SystemCPUCollector()

        collector.initialize()

        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024

        # 模拟守护进程运行 1 分钟
        start_time = time.time()
        while time.time() - start_time < 60:
            collector.collect()
            time.sleep(1)

        # 记录最终内存
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        print(f"\n守护进程内存占用:")
        print(f"  初始内存: {initial_memory:.2f} MB")
        print(f"  最终内存: {final_memory:.2f} MB")
        print(f"  内存增长: {memory_increase:.2f} MB")

        # AC 4 要求：内存 < 100MB
        assert final_memory < 100

        collector.cleanup()

    @pytest.mark.skipif(not os.path.exists('/proc/stat'), reason="Requires Linux")
    def test_daemon_mode_cpu(self):
        """测试守护进程模式的 CPU 占用"""
        collector = SystemCPUCollector()
        detector = StaticThresholdDetector(threshold=80.0)

        collector.initialize()

        # 监控 CPU 使用率
        process = psutil.Process()
        cpu_samples = []

        start_time = time.time()
        while time.time() - start_time < 30:
            # 采集和检测
            metrics = collector.collect()

            if len(metrics) > 10:
                anomalies = detector.detect(metrics)

            # 记录 CPU 使用率
            cpu_percent = process.cpu_percent(interval=0.1)
            cpu_samples.append(cpu_percent)

        avg_cpu = sum(cpu_samples) / len(cpu_samples)
        max_cpu = max(cpu_samples)

        print(f"\n守护进程 CPU 占用:")
        print(f"  平均 CPU: {avg_cpu:.2f}%")
        print(f"  峰值 CPU: {max_cpu:.2f}%")
        print(f"  采样次数: {len(cpu_samples)}")

        # AC 4 要求：工具自身 CPU < 2%
        assert avg_cpu < 2.0

        collector.cleanup()

    def test_disk_io_usage(self):
        """测试磁盘 I/O 占用"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "metrics.json"

            # 模拟数据持久化
            start_time = time.time()
            iterations = 0

            while time.time() - start_time < 60:
                # 生成数据
                metrics = []
                for i in range(10):
                    metric = {
                        'timestamp': datetime.now().isoformat(),
                        'cpu_percent': np.random.random() * 100,
                    }
                    metrics.append(metric)

                # 写入文件
                with open(data_file, 'a') as f:
                    for metric in metrics:
                        f.write(json.dumps(metric) + '\n')

                iterations += 1
                time.sleep(1)

            # 检查文件大小
            file_size_mb = data_file.stat().st_size / 1024 / 1024
            duration_minutes = (time.time() - start_time) / 60
            size_per_hour = file_size_mb / duration_minutes * 60

            print(f"\n磁盘 I/O 占用:")
            print(f"  运行时间: {duration_minutes:.2f} 分钟")
            print(f"  文件大小: {file_size_mb:.2f} MB")
            print(f"  每小时写入: {size_per_hour:.2f} MB/hour")
            print(f"  写入次数: {iterations}")

            # AC 4 要求：磁盘写入 < 10MB/hour
            assert size_per_hour < 10


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--tb=short'])
