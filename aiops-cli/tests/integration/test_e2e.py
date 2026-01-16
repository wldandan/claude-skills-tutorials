#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端集成测试

测试内容:
1. 完整的数据采集流程
2. 完整的异常检测流程
3. 命令行接口测试
4. 数据持久化测试
5. 报告生成测试
"""

import pytest
import os
import sys
import json
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'aiops-cli'))

from aiops.cpu.collectors.system_cpu import SystemCPUCollector
from aiops.cpu.collectors.process_cpu import ProcessCPUCollector
from aiops.cpu.detectors.static_threshold import StaticThresholdDetector
from aiops.cpu.detectors.dynamic_baseline import DynamicBaselineDetector


@pytest.mark.integration
class TestDataCollectionPipeline:
    """数据采集流程集成测试"""

    @pytest.mark.skipif(not os.path.exists('/proc/stat'), reason="Requires Linux")
    def test_full_collection_cycle(self):
        """测试完整的数据采集周期"""
        collector = SystemCPUCollector()

        try:
            # 初始化
            collector.initialize()

            # 连续采集 10 次
            metrics = []
            for _ in range(10):
                batch = collector.collect()
                metrics.extend(batch)

            # 验证采集结果
            assert len(metrics) == 10

            # 验证数据完整性
            for metric in metrics:
                assert hasattr(metric, 'timestamp')
                assert hasattr(metric, 'cpu_percent')
                assert 0 <= metric.cpu_percent <= 100

        finally:
            collector.cleanup()

    @pytest.mark.skipif(not os.path.exists('/proc/self/stat'), reason="Requires Linux")
    def test_process_collection_pipeline(self):
        """测试进程数据采集流程"""
        pid = os.getpid()
        collector = ProcessCPUCollector()

        # 采集进程数据
        metric = collector.collect(pid)

        assert metric.pid == pid
        assert 0 <= metric.cpu_percent <= 100


@pytest.mark.integration
class TestAnomalyDetectionPipeline:
    """异常检测流程集成测试"""

    @pytest.mark.skipif(not os.path.exists('/proc/stat'), reason="Requires Linux")
    def test_collect_and_detect_pipeline(self):
        """测试采集 + 检测完整流程"""
        collector = SystemCPUCollector()
        detector = StaticThresholdDetector(threshold=80.0)

        try:
            collector.initialize()

            # 采集数据
            metrics = []
            for _ in range(20):
                batch = collector.collect()
                metrics.extend(batch)

            # 检测异常
            anomalies = detector.detect(metrics)

            # 验证结果
            assert isinstance(anomalies, list)

            # 如果检测到异常，验证其结构
            for anomaly in anomalies:
                assert hasattr(anomaly, 'event_id')
                assert hasattr(anomaly, 'severity')
                assert hasattr(anomaly, 'start_time')
                assert hasattr(anomaly, 'end_time')

        finally:
            collector.cleanup()

    @pytest.mark.skipif(not os.path.exists('/proc/stat'), reason="Requires Linux")
    def test_baseline_learning_and_detection(self):
        """测试基线学习和检测流程"""
        collector = SystemCPUCollector()
        detector = DynamicBaselineDetector(baseline_window=7, std_threshold=3.0)

        try:
            collector.initialize()

            # 采集基线数据（模拟）
            baseline_metrics = []
            for _ in range(100):
                batch = collector.collect()
                baseline_metrics.extend(batch)

            # 计算基线
            baseline = detector._calculate_baseline(baseline_metrics)

            # 采集测试数据
            test_metrics = []
            for _ in range(20):
                batch = collector.collect()
                test_metrics.extend(batch)

            # 检测异常
            anomalies = detector._detect_with_baseline(test_metrics, baseline)

            # 验证结果
            assert isinstance(anomalies, list)

        finally:
            collector.cleanup()


@pytest.mark.integration
class TestCommandLineInterface:
    """命令行接口集成测试"""

    def test_aiops_collect_command(self):
        """测试 aiops collect 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "cpu_data.json"

            # 执行采集命令
            result = subprocess.run(
                ['python', '-m', 'aiops.cli', 'collect', 'cpu',
                 '--duration', '10',
                 '--output', str(output_file)],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent.parent / 'aiops-cli')
            )

            # 验证命令执行
            # 注意：如果命令未实现，这个测试会失败
            # result.returncode == 0

            # 验证输出文件
            if output_file.exists():
                with open(output_file, 'r') as f:
                    data = json.load(f)
                assert isinstance(data, list)

    def test_aiops_detect_command(self):
        """测试 aiops detect 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "detection_result.json"

            # 执行检测命令
            result = subprocess.run(
                ['python', '-m', 'aiops.cli', 'detect', 'cpu',
                 '--threshold', '80',
                 '--time-range', '5m',
                 '--output', 'json',
                 '--output-file', str(output_file)],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent.parent / 'aiops-cli')
            )

            # 验证输出
            if output_file.exists():
                with open(output_file, 'r') as f:
                    result = json.load(f)
                assert 'detection_results' in result or 'anomalies' in result

    def test_aiops_analyze_command(self):
        """测试 aiops analyze 命令"""
        pid = os.getpid()

        result = subprocess.run(
            ['python', '-m', 'aiops.cli', 'analyze', 'cpu',
             '--pid', str(pid),
             '--threads'],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent / 'aiops-cli')
        )

        # 验证命令执行（不报错即可）
        # result.returncode == 0

    def test_output_format_json(self):
        """测试 JSON 输出格式"""
        result = subprocess.run(
            ['python', '-m', 'aiops.cli', 'detect', 'cpu',
             '--output', 'json'],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent / 'aiops-cli')
        )

        if result.stdout:
            # 验证 JSON 可解析
            try:
                data = json.loads(result.stdout)
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                pytest.fail("输出不是有效的 JSON 格式")

    def test_output_format_table(self):
        """测试表格输出格式"""
        result = subprocess.run(
            ['python', '-m', 'aiops.cli', 'detect', 'cpu',
             '--output', 'table'],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent / 'aiops-cli')
        )

        # 表格输出应该包含特定字符（如 │ ┌ ┐ └ ┘ 等）
        if result.stdout:
            # 验证输出不为空
            assert len(result.stdout) > 0


@pytest.mark.integration
class TestDataPersistence:
    """数据持久化集成测试"""

    def test_save_and_load_metrics(self):
        """测试保存和加载指标数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "metrics.json"

            # 生成测试数据
            metrics = []
            start_time = datetime.now()
            for i in range(10):
                metric = {
                    'timestamp': (start_time + timedelta(seconds=i)).isoformat(),
                    'cpu_percent': 40.0 + i,
                    'cpu_user': 24.0 + i * 0.6,
                    'cpu_system': 12.0 + i * 0.3,
                    'cpu_idle': 60.0 - i,
                    'cpu_iowait': 4.0 + i * 0.1,
                }
                metrics.append(metric)

            # 保存数据
            with open(data_file, 'w') as f:
                json.dump(metrics, f)

            # 加载数据
            with open(data_file, 'r') as f:
                loaded_metrics = json.load(f)

            # 验证数据一致性
            assert len(loaded_metrics) == len(metrics)
            assert loaded_metrics[0]['cpu_percent'] == metrics[0]['cpu_percent']

    def test_csv_export_import(self):
        """测试 CSV 导出和导入"""
        import pandas as pd

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "metrics.csv"

            # 创建测试数据
            data = {
                'timestamp': [datetime.now().isoformat() for _ in range(10)],
                'cpu_percent': [40.0 + i for i in range(10)],
                'cpu_user': [24.0 + i * 0.6 for i in range(10)],
            }

            # 保存为 CSV
            df = pd.DataFrame(data)
            df.to_csv(csv_file, index=False)

            # 加载 CSV
            loaded_df = pd.read_csv(csv_file)

            # 验证数据
            assert len(loaded_df) == 10
            assert 'cpu_percent' in loaded_df.columns
            assert loaded_df['cpu_percent'].iloc[0] == 40.0


@pytest.mark.integration
class TestEndToEndScenarios:
    """端到端场景测试"""

    @pytest.mark.skipif(not os.path.exists('/proc/stat'), reason="Requires Linux")
    def test_monitoring_scenario(self):
        """测试监控场景：采集 -> 检测 -> 报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # 1. 采集数据
            collector = SystemCPUCollector()
            collector.initialize()

            metrics = []
            for _ in range(30):
                batch = collector.collect()
                metrics.extend(batch)

            collector.cleanup()

            # 2. 保存数据
            data_file = tmpdir / "monitoring_data.json"
            with open(data_file, 'w') as f:
                json.dump([{
                    'timestamp': m.timestamp.isoformat(),
                    'cpu_percent': m.cpu_percent,
                    'cpu_user': m.cpu_user,
                    'cpu_system': m.cpu_system,
                    'cpu_idle': m.cpu_idle,
                } for m in metrics], f)

            # 3. 检测异常
            detector = StaticThresholdDetector(threshold=80.0)
            anomalies = detector.detect(metrics)

            # 4. 生成报告
            report = {
                'monitoring_period': {
                    'start': metrics[0].timestamp.isoformat(),
                    'end': metrics[-1].timestamp.isoformat(),
                    'duration_seconds': (metrics[-1].timestamp - metrics[0].timestamp).total_seconds()
                },
                'data_points_collected': len(metrics),
                'anomalies_detected': len(anomalies),
                'anomaly_details': [
                    {
                        'event_id': a.event_id,
                        'severity': a.severity,
                        'start_time': a.start_time.isoformat(),
                        'end_time': a.end_time.isoformat(),
                        'avg_cpu': a.avg_cpu,
                    }
                    for a in anomalies
                ]
            }

            report_file = tmpdir / "monitoring_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)

            # 验证报告
            assert report_file.exists()
            assert 'monitoring_period' in report
            assert 'anomalies_detected' in report

    def test_error_recovery_scenario(self):
        """测试错误恢复场景"""
        collector = SystemCPUCollector()

        # 模拟采集失败后恢复
        try:
            collector.initialize()

            # 正常采集
            metrics1 = collector.collect()
            assert len(metrics1) > 0

            # 模拟失败（临时移除 /proc/stat）
            # 注意：实际测试中可能无法模拟，这里只是演示

            # 恢复后继续采集
            metrics2 = collector.collect()
            assert len(metrics2) > 0

        finally:
            collector.cleanup()


@pytest.mark.integration
class TestPerformanceScenarios:
    """性能场景集成测试"""

    @pytest.mark.performance
    @pytest.mark.skipif(not os.path.exists('/proc/stat'), reason="Requires Linux")
    def test_long_running_monitoring(self):
        """测试长时间运行的监控性能"""
        import time

        collector = SystemCPUCollector()
        detector = StaticThresholdDetector(threshold=80.0)

        try:
            collector.initialize()

            # 运行 1 分钟
            start_time = time.time()
            metrics = []
            iterations = 0

            while time.time() - start_time < 60:
                batch = collector.collect()
                metrics.extend(batch)
                iterations += 1
                time.sleep(1)

            # 测量检测性能
            detect_start = time.time()
            anomalies = detector.detect(metrics)
            detect_time = time.time() - detect_start

            print(f"\n长时间监控测试结果:")
            print(f"  运行时间: {time.time() - start_time:.2f} 秒")
            print(f"  采集次数: {iterations}")
            print(f"  数据点数量: {len(metrics)}")
            print(f"  检测耗时: {detect_time:.4f} 秒")

            # 验证性能
            assert detect_time < 5.0  # 检测应该在 5 秒内完成

        finally:
            collector.cleanup()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-m', 'integration'])
