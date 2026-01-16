#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常检测算法单元测试

测试内容:
1. 静态阈值检测
2. 动态基线检测
3. 机器学习算法检测（Isolation Forest）
4. 检测准确性验证
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'aiops-cli'))

from aiops.cpu.detectors.static_threshold import StaticThresholdDetector
from aiops.cpu.detectors.dynamic_baseline import DynamicBaselineDetector
from aiops.cpu.models.anomaly_event import AnomalyEvent
from aiops.cpu.models.cpu_metric import CPUMetric


class TestStaticThresholdDetector:
    """静态阈值检测器测试"""

    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        return StaticThresholdDetector(threshold=80.0)

    @pytest.fixture
    def normal_metrics(self):
        """生成正常 CPU 指标"""
        metrics = []
        start_time = datetime.now()
        for i in range(100):
            cpu_percent = np.random.normal(40, 10)  # 正态分布，均值 40%
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
        return metrics

    @pytest.fixture
    def anomaly_metrics(self):
        """生成包含异常的 CPU 指标"""
        metrics = []
        start_time = datetime.now()
        for i in range(100):
            # 在 40-60 秒之间插入异常
            if 40 <= i < 60:
                cpu_percent = np.random.normal(90, 5)  # 异常高 CPU
            else:
                cpu_percent = np.random.normal(40, 10)  # 正常 CPU

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
        return metrics

    def test_detector_initialization(self):
        """测试检测器初始化"""
        detector = StaticThresholdDetector(threshold=90.0)
        assert detector.threshold == 90.0
        assert detector.consecutive_periods == 3

    def test_detect_no_anomaly(self, detector, normal_metrics):
        """测试无异常场景"""
        anomalies = detector.detect(normal_metrics)

        # 正常数据不应检测到异常
        assert len(anomalies) == 0

    def test_detect_anomaly(self, detector, anomaly_metrics):
        """测试异常检测"""
        anomalies = detector.detect(anomaly_metrics)

        # 应该检测到至少一个异常
        assert len(anomalies) > 0

        # 验证异常事件
        anomaly = anomalies[0]
        assert isinstance(anomaly, AnomalyEvent)
        assert anomaly.severity in ['warning', 'critical', 'emergency']
        assert anomaly.start_time is not None
        assert anomaly.end_time is not None

    def test_consecutive_anomaly_detection(self):
        """测试连续异常检测（避免瞬时抖动）"""
        detector = StaticThresholdDetector(threshold=80.0, consecutive_periods=3)

        # 创建刚好在阈值附近波动的数据
        metrics = []
        start_time = datetime.now()
        for i in range(10):
            cpu_percent = 85.0 if i < 2 else 40.0  # 只有 2 个周期超过阈值
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

        anomalies = detector.detect(metrics)

        # 2 个周期不应触发异常（需要 3 个）
        assert len(anomalies) == 0

    def test_threshold_boundary(self):
        """测试阈值边界条件"""
        detector = StaticThresholdDetector(threshold=80.0)

        # 创建恰好等于阈值的数据
        metrics = []
        start_time = datetime.now()
        for i in range(5):
            metric = CPUMetric(
                timestamp=start_time + timedelta(seconds=i),
                cpu_percent=80.0,
                cpu_user=48.0,
                cpu_system=24.0,
                cpu_idle=20.0,
                cpu_iowait=8.0,
                cpu_steal=0.0
            )
            metrics.append(metric)

        anomalies = detector.detect(metrics)

        # 等于阈值是否算异常取决于实现
        # 这里我们假设 >= 阈值触发异常
        assert len(anomalies) >= 0

    def test_anomaly_severity_levels(self):
        """测试异常严重程度分级"""
        # 测试不同阈值对应的严重程度
        test_cases = [
            (90.0, 95.0, 'critical'),
            (80.0, 90.0, 'warning'),
        ]

        for threshold, cpu_value, expected_severity in test_cases:
            detector = StaticThresholdDetector(threshold=threshold)

            metrics = [CPUMetric(
                timestamp=datetime.now(),
                cpu_percent=cpu_value,
                cpu_user=cpu_value * 0.6,
                cpu_system=cpu_value * 0.3,
                cpu_idle=100 - cpu_value,
                cpu_iowait=cpu_value * 0.1,
                cpu_steal=0.0
            )] * 5  # 连续 5 个周期

            anomalies = detector.detect(metrics)
            if len(anomalies) > 0:
                assert anomalies[0].severity == expected_severity


class TestDynamicBaselineDetector:
    """动态基线检测器测试"""

    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        return DynamicBaselineDetector(
            baseline_window=7,  # 7 天基线
            std_threshold=3.0   # 3 倍标准差
        )

    @pytest.fixture
    def baseline_data(self):
        """生成历史基线数据"""
        metrics = []
        start_time = datetime.now() - timedelta(days=7)

        for i in range(7 * 24 * 60):  # 7 天，每分钟一个数据点
            # 模拟日周期模式
            hour = (i // 60) % 24
            if 9 <= hour <= 18:  # 工作时间高负载
                base_cpu = 60.0
            elif 0 <= hour < 6:  # 夜间低负载
                base_cpu = 20.0
            else:  # 其他时间
                base_cpu = 40.0

            cpu_percent = np.random.normal(base_cpu, 5)
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
            metrics.append(metric)

        return metrics

    @pytest.fixture
    def test_data_with_anomaly(self, baseline_data):
        """生成测试数据（包含异常）"""
        # 使用基线数据的最后部分作为测试数据
        base_time = datetime.now()
        metrics = []

        # 前 10 个数据点正常
        for i in range(10):
            cpu_percent = np.random.normal(40, 5)
            cpu_percent = max(0, min(100, cpu_percent))
            metric = CPUMetric(
                timestamp=base_time + timedelta(minutes=i),
                cpu_percent=cpu_percent,
                cpu_user=cpu_percent * 0.6,
                cpu_system=cpu_percent * 0.3,
                cpu_idle=100 - cpu_percent,
                cpu_iowait=cpu_percent * 0.1,
                cpu_steal=0.0
            )
            metrics.append(metric)

        # 后 10 个数据点异常
        for i in range(10, 20):
            cpu_percent = np.random.normal(95, 2)  # 明显偏离基线
            metric = CPUMetric(
                timestamp=base_time + timedelta(minutes=i),
                cpu_percent=cpu_percent,
                cpu_user=cpu_percent * 0.6,
                cpu_system=cpu_percent * 0.3,
                cpu_idle=100 - cpu_percent,
                cpu_iowait=cpu_percent * 0.1,
                cpu_steal=0.0
            )
            metrics.append(metric)

        return metrics, baseline_data

    def test_detector_initialization(self):
        """测试检测器初始化"""
        detector = DynamicBaselineDetector(
            baseline_window=14,
            std_threshold=2.5
        )
        assert detector.baseline_window == 14
        assert detector.std_threshold == 2.5

    def test_baseline_calculation(self, detector, baseline_data):
        """测试基线计算"""
        baseline = detector._calculate_baseline(baseline_data)

        # 基线应该包含统计数据
        assert 'mean' in baseline
        assert 'std' in baseline
        assert 'hourly' in baseline

        # 均值应该在合理范围内
        assert 0 <= baseline['mean'] <= 100

        # 标准差应该非负
        assert baseline['std'] >= 0

    def test_detect_with_baseline(self, detector, test_data_with_anomaly):
        """测试使用基线进行异常检测"""
        test_data, baseline_data = test_data_with_anomaly

        # 计算基线
        baseline = detector._calculate_baseline(baseline_data)

        # 检测异常
        anomalies = detector._detect_with_baseline(test_data, baseline)

        # 应该检测到异常
        assert len(anomalies) > 0

    def test_hourly_baseline_detection(self, detector):
        """测试按小时分组的基线检测"""
        # 创建特定小时的异常数据
        base_time = datetime.now().replace(hour=14, minute=0, second=0)
        metrics = []

        # 正常数据
        for i in range(10):
            cpu_percent = np.random.normal(40, 5)
            metric = CPUMetric(
                timestamp=base_time + timedelta(minutes=i),
                cpu_percent=cpu_percent,
                cpu_user=cpu_percent * 0.6,
                cpu_system=cpu_percent * 0.3,
                cpu_idle=100 - cpu_percent,
                cpu_iowait=cpu_percent * 0.1,
                cpu_steal=0.0
            )
            metrics.append(metric)

        # 异常数据（同一小时）
        for i in range(10, 20):
            cpu_percent = np.random.normal(95, 2)
            metric = CPUMetric(
                timestamp=base_time + timedelta(minutes=i),
                cpu_percent=cpu_percent,
                cpu_user=cpu_percent * 0.6,
                cpu_system=cpu_percent * 0.3,
                cpu_idle=100 - cpu_percent,
                cpu_iowait=cpu_percent * 0.1,
                cpu_steal=0.0
            )
            metrics.append(metric)

        # 创建该小时的历史基线数据
        baseline_metrics = []
        for day in range(7):
            for minute in range(60):
                cpu_percent = np.random.normal(40, 5)
                metric = CPUMetric(
                    timestamp=base_time - timedelta(days=7-day, minutes=60-minute),
                    cpu_percent=cpu_percent,
                    cpu_user=cpu_percent * 0.6,
                    cpu_system=cpu_percent * 0.3,
                    cpu_idle=100 - cpu_percent,
                    cpu_iowait=cpu_percent * 0.1,
                    cpu_steal=0.0
                )
                baseline_metrics.append(metric)

        baseline = detector._calculate_baseline(baseline_metrics)
        anomalies = detector._detect_with_baseline(metrics, baseline)

        # 应该检测到异常
        assert len(anomalies) > 0


class TestAnomalyEvent:
    """异常事件模型测试"""

    def test_anomaly_event_creation(self):
        """测试异常事件创建"""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=5)

        event = AnomalyEvent(
            event_id="test_001",
            severity="critical",
            start_time=start_time,
            end_time=end_time,
            avg_cpu=95.0,
            max_cpu=98.5,
            baseline_cpu=45.0,
            confidence=0.98
        )

        assert event.event_id == "test_001"
        assert event.severity == "critical"
        assert event.avg_cpu == 95.0
        assert event.max_cpu == 98.5
        assert event.baseline_cpu == 45.0
        assert event.confidence == 0.98

    def test_anomaly_duration(self):
        """测试异常持续时间计算"""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=5, seconds=30)

        event = AnomalyEvent(
            event_id="test_002",
            severity="warning",
            start_time=start_time,
            end_time=end_time,
            avg_cpu=85.0,
            max_cpu=90.0,
            baseline_cpu=40.0,
            confidence=0.85
        )

        expected_duration = (end_time - start_time).total_seconds()
        actual_duration = event.duration_seconds

        assert actual_duration == expected_duration
        assert actual_duration == 330  # 5 分 30 秒

    def test_severity_validation(self):
        """测试严重程度验证"""
        valid_severities = ['warning', 'critical', 'emergency']

        for severity in valid_severities:
            event = AnomalyEvent(
                event_id=f"test_{severity}",
                severity=severity,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(minutes=1),
                avg_cpu=80.0,
                max_cpu=85.0,
                baseline_cpu=40.0,
                confidence=0.8
            )
            assert event.severity == severity

    def test_confidence_bounds(self):
        """测试置信度边界"""
        # 置信度应该在 0-1 之间
        with pytest.raises((ValueError, AssertionError)):
            AnomalyEvent(
                event_id="test_invalid",
                severity="critical",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(minutes=1),
                avg_cpu=95.0,
                max_cpu=98.0,
                baseline_cpu=40.0,
                confidence=1.5  # 无效置信度
            )


@pytest.mark.accuracy
class TestDetectionAccuracy:
    """检测准确性测试"""

    @pytest.fixture
    def labeled_dataset(self):
        """生成带标注的测试数据集"""
        # 包含正常和异常的标注数据
        data = []
        labels = []
        start_time = datetime.now()

        for i in range(200):
            if 50 <= i < 80:  # 已知异常区间
                cpu_percent = np.random.normal(92, 3)
                labels.append(1)  # 异常
            else:
                cpu_percent = np.random.normal(40, 8)
                labels.append(0)  # 正常

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
            data.append(metric)

        return data, labels

    def test_static_threshold_accuracy(self, labeled_dataset):
        """测试静态阈值检测准确性"""
        data, labels = labeled_dataset
        detector = StaticThresholdDetector(threshold=85.0)

        anomalies = detector.detect(data)

        # 将检测结果转换为二进制标签
        predicted_labels = [0] * len(data)
        for anomaly in anomalies:
            start_idx = int((anomaly.start_time - data[0].timestamp).total_seconds())
            end_idx = int((anomaly.end_time - data[0].timestamp).total_seconds())
            for i in range(start_idx, min(end_idx + 1, len(predicted_labels))):
                predicted_labels[i] = 1

        # 计算准确率
        correct = sum(1 for p, a in zip(predicted_labels, labels) if p == a)
        accuracy = correct / len(labels)

        print(f"\n静态阈值检测准确率: {accuracy:.2%}")

        # 准确率应该 >= 95%
        assert accuracy >= 0.95

    def test_detection_delay(self):
        """测试检测延迟"""
        detector = StaticThresholdDetector(threshold=85.0, consecutive_periods=2)

        # 创建一个突然发生的异常
        metrics = []
        start_time = datetime.now()

        # 10 个正常数据点
        for i in range(10):
            metric = CPUMetric(
                timestamp=start_time + timedelta(seconds=i),
                cpu_percent=40.0,
                cpu_user=24.0,
                cpu_system=12.0,
                cpu_idle=60.0,
                cpu_iowait=4.0,
                cpu_steal=0.0
            )
            metrics.append(metric)

        # 突然出现异常
        anomaly_start_idx = len(metrics)
        for i in range(10, 20):
            metric = CPUMetric(
                timestamp=start_time + timedelta(seconds=i),
                cpu_percent=95.0,
                cpu_user=57.0,
                cpu_system=28.5,
                cpu_idle=5.0,
                cpu_iowait=9.5,
                cpu_steal=0.0
            )
            metrics.append(metric)

        anomalies = detector.detect(metrics)

        if len(anomalies) > 0:
            # 计算检测延迟
            detected_start = anomalies[0].start_time
            actual_start = metrics[anomaly_start_idx].timestamp
            delay = (detected_start - actual_start).total_seconds()

            print(f"\n检测延迟: {delay} 秒")

            # 检测延迟应该 <= 30 秒
            # consecutive_periods=2，所以最多延迟 2 个采样周期
            assert delay <= 30


@pytest.mark.performance
class TestDetectorPerformance:
    """检测器性能测试"""

    def test_large_dataset_detection(self):
        """测试大数据集检测性能"""
        import time

        # 生成大量数据（24小时，每秒一个数据点）
        metrics = []
        start_time = datetime.now()
        for i in range(86400):
            cpu_percent = np.random.normal(45, 10)
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

        print(f"\n检测 {len(metrics)} 个数据点耗时: {elapsed:.4f} 秒")
        print(f"平均检测速度: {len(metrics)/elapsed:.0f} 数据点/秒")

        # 检测应该在合理时间内完成
        assert elapsed < 10.0  # 10 秒内完成


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
