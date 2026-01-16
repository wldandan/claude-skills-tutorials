#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 配置和共享 fixtures

提供测试所需的共享 fixtures、钩子和配置
"""

import pytest
import os
import sys
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'aiops-cli'))


# ============================================================================
# 全局配置
# ============================================================================

def pytest_configure(config):
    """pytest 配置钩子"""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    # 自动标记慢速测试
    for item in items:
        if "slow" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)

        # 如果测试需要 Linux 但不在 Linux 上，自动跳过
        if "linux_only" in item.keywords and sys.platform != "linux":
            item.add_marker(pytest.mark.skip(reason="Requires Linux"))

        # 如果测试需要 root 但不是 root，自动跳过
        if "requires_root" in item.keywords and os.geteuid() != 0:
            item.add_marker(pytest.mark.skip(reason="Requires root privileges"))


# ============================================================================
# 共享 Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root():
    """项目根目录"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def aiops_cli_path(project_root):
    """aiops-cli 路径"""
    return project_root / "aiops-cli"


@pytest.fixture(scope="session")
def tests_path(project_root):
    """测试目录路径"""
    return project_root / "tests"


@pytest.fixture(scope="session")
def chaos_path(project_root):
    """混沌工程工具路径"""
    return project_root / "chaos"


@pytest.fixture(scope="session")
def test_data_path(tests_path):
    """测试数据路径"""
    path = tests_path / "fixtures" / "test_data"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def temp_dir():
    """临时目录 fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir):
    """临时文件 fixture"""
    def _create_temp_file(name, content=""):
        file_path = temp_dir / name
        file_path.write_text(content)
        return file_path

    return _create_temp_file


# ============================================================================
# Mock 数据 Fixtures
# ============================================================================

@pytest.fixture
def sample_cpu_metrics():
    """生成示例 CPU 指标"""
    metrics = []
    start_time = datetime.now()

    for i in range(100):
        cpu_percent = np.random.normal(45, 10)
        cpu_percent = max(0, min(100, cpu_percent))

        from aiops.cpu.models.cpu_metric import CPUMetric
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
def sample_anomaly_metrics():
    """生成包含异常的 CPU 指标"""
    metrics = []
    start_time = datetime.now()

    for i in range(100):
        # 在 40-60 秒之间插入异常
        if 40 <= i < 60:
            cpu_percent = np.random.normal(92, 3)  # 异常高 CPU
        else:
            cpu_percent = np.random.normal(40, 10)  # 正常 CPU

        cpu_percent = max(0, min(100, cpu_percent))

        from aiops.cpu.models.cpu_metric import CPUMetric
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
def sample_baseline_metrics():
    """生成历史基线数据（7 天）"""
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

        from aiops.cpu.models.cpu_metric import CPUMetric
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
def mock_proc_stat_content():
    """模拟 /proc/stat 内容"""
    return "cpu  2255 34 2290 22625563 6290 127 456 0 0 0\n"


@pytest.fixture
def mock_proc_pid_stat_content():
    """模拟 /proc/[pid]/stat 内容"""
    return "1234 (test_process) R 1 1234 1234 0 -1 4194304 100 0 0 0 500 100 0 0 20 0 1 0 12345678 123456789"


# ============================================================================
# 测试数据集 Fixtures
# ============================================================================

@pytest.fixture
def accuracy_dataset_path(test_data_path):
    """准确性测试数据集路径"""
    dataset_path = test_data_path / "accuracy_dataset.json"

    if not dataset_path.exists():
        # 生成测试数据集
        from tests.mocks.generate_test_data import MixedScenarioGenerator

        generator = MixedScenarioGenerator(seed=42)
        data = generator.generate_day_with_anomalies(datetime.now(), anomaly_count=5)

        with open(dataset_path, 'w') as f:
            json.dump(data, f)

    return dataset_path


@pytest.fixture
def performance_dataset_path(test_data_path):
    """性能测试数据集路径"""
    dataset_path = test_data_path / "performance_dataset.json"

    if not dataset_path.exists():
        # 生成大数据集
        from tests.mocks.generate_test_data import NormalDataGenerator

        generator = NormalDataGenerator(base_cpu=40, variance=10, seed=42)
        data = generator.generate_time_series(
            datetime.now(),
            duration_minutes=1440,  # 24 小时
            interval_seconds=1
        )

        with open(dataset_path, 'w') as f:
            json.dump(data, f)

    return dataset_path


# ============================================================================
# 采集器 Fixtures
# ============================================================================

@pytest.fixture
def system_cpu_collector():
    """系统 CPU 采集器 fixture"""
    from aiops.cpu.collectors.system_cpu import SystemCPUCollector
    collector = SystemCPUCollector()

    yield collector

    # 清理
    try:
        collector.cleanup()
    except:
        pass


@pytest.fixture
def process_cpu_collector():
    """进程 CPU 采集器 fixture"""
    from aiops.cpu.collectors.process_cpu import ProcessCPUCollector
    return ProcessCPUCollector()


# ============================================================================
# 检测器 Fixtures
# ============================================================================

@pytest.fixture
def static_threshold_detector():
    """静态阈值检测器 fixture"""
    from aiops.cpu.detectors.static_threshold import StaticThresholdDetector
    return StaticThresholdDetector(threshold=80.0)


@pytest.fixture
def dynamic_baseline_detector():
    """动态基线检测器 fixture"""
    from aiops.cpu.detectors.dynamic_baseline import DynamicBaselineDetector
    return DynamicBaselineDetector(baseline_window=7, std_threshold=3.0)


# ============================================================================
# 性能测试 Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def benchmark_iterations():
    """性能测试迭代次数配置"""
    return {
        "small": 100,
        "medium": 1000,
        "large": 10000,
        "xlarge": 100000,
    }


@pytest.fixture
def performance_timer():
    """性能计时器 fixture"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.elapsed = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()
            self.elapsed = self.end_time - self.start_time
            return self.elapsed

        def __enter__(self):
            self.start()
            return self

        def __exit__(self, *args):
            self.stop()

    return Timer


# ============================================================================
# 跳过条件
# ============================================================================

def pytest_runtest_setup(item):
    """测试运行前的设置"""
    # Linux 检查
    if item.get_closest_marker("linux_only") and sys.platform != "linux":
        pytest.skip("Test requires Linux")

    # Root 权限检查
    if item.get_closest_marker("requires_root") and os.geteuid() != 0:
        pytest.skip("Test requires root privileges")

    # /proc 文件系统检查
    if item.get_closest_marker("requires_proc") and not os.path.exists('/proc/stat'):
        pytest.skip("Test requires /proc filesystem")


# ============================================================================
# 测试报告钩子
# ============================================================================

def pytest_html_results_summary(prefix, summary, postfix):
    """自定义 HTML 测试报告摘要"""
    prefix.extend([
        "<h2>测试环境信息</h2>",
        f"<p>操作系统: {sys.platform}</p>",
        f"<p>Python 版本: {sys.version}</p>",
        f"<p>测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
    ])


@pytest.fixture(autouse=True)
def add_test_summary(request, record_testsuite_property):
    """为每个测试添加摘要信息"""
    record_testsuite_property("test_id", request.node.nodeid)
    record_testsuite_property("test_marker", list(request.node.keywords.keys()))
