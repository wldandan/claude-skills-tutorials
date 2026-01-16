#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock 数据生成器 - 生成测试用的 CPU 指标数据

功能:
1. 生成系统级 CPU 指标数据
2. 生成进程级 CPU 指标数据
3. 生成异常场景数据
4. 生成时间序列数据
"""

import os
import sys
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path


class CPUMetricGenerator:
    """CPU 指标数据生成器"""

    def __init__(self, seed: Optional[int] = None):
        """
        初始化数据生成器

        Args:
            seed: 随机种子，用于可重复的数据生成
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def generate_system_metric(self, cpu_percent: float, timestamp: datetime,
                               per_core: bool = False, num_cores: int = 4) -> Dict:
        """
        生成系统级 CPU 指标

        Args:
            cpu_percent: CPU 使用率 (0-100)
            timestamp: 时间戳
            per_core: 是否生成每核数据
            num_cores: CPU 核心数量

        Returns:
            CPU 指标字典
        """
        # 确保 CPU 使用率在有效范围内
        cpu_percent = max(0, min(100, cpu_percent))

        # 计算各时间分量
        idle = max(0, 100 - cpu_percent)
        user = cpu_percent * random.uniform(0.5, 0.7)
        system = cpu_percent * random.uniform(0.2, 0.3)
        iowait = cpu_percent - user - system

        metric = {
            'timestamp': timestamp.isoformat(),
            'cpu_percent': round(cpu_percent, 2),
            'user_percent': round(user, 2),
            'system_percent': round(system, 2),
            'idle_percent': round(idle, 2),
            'iowait_percent': round(max(0, iowait), 2),
        }

        if per_core:
            metric['cores'] = []
            for i in range(num_cores):
                # 每核的 CPU 使用率略有不同
                core_variance = random.uniform(-5, 5)
                core_cpu = max(0, min(100, cpu_percent + core_variance))

                core_idle = max(0, 100 - core_cpu)
                core_user = core_cpu * random.uniform(0.5, 0.7)
                core_system = core_cpu * random.uniform(0.2, 0.3)
                core_iowait = core_cpu - core_user - core_system

                metric['cores'].append({
                    'core_id': i,
                    'cpu_percent': round(core_cpu, 2),
                    'user_percent': round(core_user, 2),
                    'system_percent': round(core_system, 2),
                    'idle_percent': round(core_idle, 2),
                    'iowait_percent': round(max(0, core_iowait), 2),
                })

        return metric

    def generate_process_metric(self, pid: int, name: str, cpu_percent: float,
                                timestamp: datetime, num_threads: int = 1) -> Dict:
        """
        生成进程级 CPU 指标

        Args:
            pid: 进程 ID
            name: 进程名称
            cpu_percent: CPU 使用率
            timestamp: 时间戳
            num_threads: 线程数量

        Returns:
            进程指标字典
        """
        cpu_percent = max(0, min(100, cpu_percent))

        metric = {
            'pid': pid,
            'name': name,
            'timestamp': timestamp.isoformat(),
            'cpu_percent': round(cpu_percent, 2),
            'num_threads': num_threads,
            'user': f'user_{pid % 10}',
            'threads': []
        }

        # 生成线程数据
        for i in range(num_threads):
            thread_cpu = cpu_percent / num_threads * random.uniform(0.8, 1.2)
            metric['threads'].append({
                'tid': f'{pid}.{i}',
                'cpu_percent': round(max(0, min(100, thread_cpu)), 2),
                'name': f'{name}_thread_{i}'
            })

        return metric


class NormalDataGenerator(CPUMetricGenerator):
    """正常负载数据生成器"""

    def __init__(self, base_cpu: float = 40.0, variance: float = 10.0, seed: Optional[int] = None):
        """
        初始化正常数据生成器

        Args:
            base_cpu: 基础 CPU 使用率
            variance: 波动范围
            seed: 随机种子
        """
        super().__init__(seed)
        self.base_cpu = base_cpu
        self.variance = variance

    def generate_time_series(self, start_time: datetime, duration_minutes: int,
                             interval_seconds: int = 1) -> List[Dict]:
        """
        生成正常负载的时间序列数据

        Args:
            start_time: 开始时间
            duration_minutes: 持续时间（分钟）
            interval_seconds: 采样间隔（秒）

        Returns:
            时间序列数据列表
        """
        data = []
        current_time = start_time
        end_time = start_time + timedelta(minutes=duration_minutes)

        while current_time < end_time:
            # 正态分布的 CPU 使用率
            cpu_percent = random.gauss(self.base_cpu, self.variance)
            cpu_percent = max(5, min(95, cpu_percent))  # 限制在 5-95% 之间

            metric = self.generate_system_metric(cpu_percent, current_time)
            data.append(metric)

            current_time += timedelta(seconds=interval_seconds)

        return data


class AnomalyDataGenerator(CPUMetricGenerator):
    """异常数据生成器"""

    def generate_spike(self, base_cpu: float, spike_cpu: float,
                       start_time: datetime, duration_seconds: int,
                       interval_seconds: int = 1) -> List[Dict]:
        """
        生成 CPU 尖峰异常数据

        Args:
            base_cpu: 基线 CPU 使用率
            spike_cpu: 尖峰 CPU 使用率
            start_time: 开始时间
            duration_seconds: 尖峰持续时间（秒）
            interval_seconds: 采样间隔（秒）

        Returns:
            时间序列数据
        """
        data = []
        current_time = start_time
        end_time = start_time + timedelta(seconds=duration_seconds)

        while current_time < end_time:
            # 使用 sigmoid 函数平滑过渡
            elapsed = (current_time - start_time).total_seconds()
            progress = elapsed / duration_seconds

            # Sigmoid 形状的尖峰
            spike_factor = 1 / (1 + np.exp(-10 * (progress - 0.5)))
            spike_factor = (spike_factor - 0.5) * 2  # 归一化到 0-1

            cpu_percent = base_cpu + (spike_cpu - base_cpu) * spike_factor
            cpu_percent += random.gauss(0, 2)  # 添加随机噪声
            cpu_percent = max(0, min(100, cpu_percent))

            metric = self.generate_system_metric(cpu_percent, current_time)
            data.append(metric)

            current_time += timedelta(seconds=interval_seconds)

        return data

    def generate_step_anomaly(self, base_cpu: float, anomaly_cpu: float,
                              start_time: datetime, duration_minutes: int,
                              interval_seconds: int = 1) -> List[Dict]:
        """
        生成阶梯式异常（突发并持续）

        Args:
            base_cpu: 基线 CPU 使用率
            anomaly_cpu: 异常 CPU 使用率
            start_time: 开始时间
            duration_minutes: 持续时间（分钟）
            interval_seconds: 采样间隔（秒）

        Returns:
            时间序列数据
        """
        data = []
        current_time = start_time
        end_time = start_time + timedelta(minutes=duration_minutes)

        while current_time < end_time:
            # 前 20% 正常，然后突然跳到异常水平
            elapsed = (current_time - start_time).total_seconds()
            total_seconds = duration_minutes * 60
            progress = elapsed / total_seconds

            if progress < 0.2:
                cpu_percent = base_cpu + random.gauss(0, 3)
            else:
                cpu_percent = anomaly_cpu + random.gauss(0, 3)

            cpu_percent = max(0, min(100, cpu_percent))

            metric = self.generate_system_metric(cpu_percent, current_time)
            data.append(metric)

            current_time += timedelta(seconds=interval_seconds)

        return data

    def generate_periodic_anomaly(self, base_cpu: float, peak_cpu: float,
                                  start_time: datetime, duration_minutes: int,
                                  period_minutes: int = 5,
                                  interval_seconds: int = 1) -> List[Dict]:
        """
        生成周期性异常（模拟定时任务）

        Args:
            base_cpu: 基线 CPU 使用率
            peak_cpu: 峰值 CPU 使用率
            start_time: 开始时间
            duration_minutes: 持续时间（分钟）
            period_minutes: 周期时长（分钟）
            interval_seconds: 采样间隔（秒）

        Returns:
            时间序列数据
        """
        data = []
        current_time = start_time
        end_time = start_time + timedelta(minutes=duration_minutes)
        period_seconds = period_minutes * 60

        while current_time < end_time:
            # 使用正弦波模拟周期性
            elapsed = (current_time - start_time).total_seconds()
            phase = (elapsed % period_seconds) / period_seconds

            # 在周期中间达到峰值
            spike_factor = np.sin(phase * 2 * np.pi)
            spike_factor = max(0, spike_factor)  # 只取正半周

            cpu_percent = base_cpu + (peak_cpu - base_cpu) * spike_factor
            cpu_percent += random.gauss(0, 2)
            cpu_percent = max(0, min(100, cpu_percent))

            metric = self.generate_system_metric(cpu_percent, current_time)
            data.append(metric)

            current_time += timedelta(seconds=interval_seconds)

        return data


class MixedScenarioGenerator:
    """混合场景生成器 - 组合多种模式"""

    def __init__(self, seed: Optional[int] = None):
        self.generator = CPUMetricGenerator(seed)
        self.normal_gen = NormalDataGenerator(seed=seed)
        self.anomaly_gen = AnomalyDataGenerator(seed=seed)

    def generate_realistic_day(self, date: datetime) -> List[Dict]:
        """
        生成一天的真实 CPU 使用模式

        Args:
            date: 日期

        Returns:
            24小时的时间序列数据
        """
        all_data = []

        # 0-6点：夜间低负载
        night_data = self.normal_gen.generate_time_series(
            date.replace(hour=0, minute=0, second=0),
            duration_minutes=360,
            interval_seconds=60
        )
        all_data.extend(night_data)

        # 6-9点：早晨爬升
        for minute in range(0, 180, 1):
            cpu = 30 + (minute / 180) * 30  # 30% -> 60%
            timestamp = date.replace(hour=6, minute=0, second=0) + timedelta(minutes=minute)
            metric = self.generator.generate_system_metric(cpu, timestamp)
            all_data.append(metric)

        # 9-12点：上午工作高峰
        morning_data = self.normal_gen.generate_time_series(
            date.replace(hour=9, minute=0, second=0),
            duration_minutes=180,
            interval_seconds=60
        )
        # 修改基础 CPU 使用率
        for metric in morning_data:
            metric['cpu_percent'] = min(95, metric['cpu_percent'] + 20)
        all_data.extend(morning_data)

        # 12-13点：午休下降
        for minute in range(0, 60, 1):
            cpu = 60 - (minute / 60) * 20  # 60% -> 40%
            timestamp = date.replace(hour=12, minute=0, second=0) + timedelta(minutes=minute)
            metric = self.generator.generate_system_metric(cpu, timestamp)
            all_data.append(metric)

        # 13-18点：下午工作
        afternoon_data = self.normal_gen.generate_time_series(
            date.replace(hour=13, minute=0, second=0),
            duration_minutes=300,
            interval_seconds=60
        )
        for metric in afternoon_data:
            metric['cpu_percent'] = min(95, metric['cpu_percent'] + 15)
        all_data.extend(afternoon_data)

        # 18-24点：晚间下降
        evening_data = self.normal_gen.generate_time_series(
            date.replace(hour=18, minute=0, second=0),
            duration_minutes=360,
            interval_seconds=60
        )
        for metric in evening_data:
            metric['cpu_percent'] = max(10, metric['cpu_percent'] - 10)
        all_data.extend(evening_data)

        return all_data

    def generate_day_with_anomalies(self, date: datetime,
                                    anomaly_count: int = 3) -> List[Dict]:
        """
        生成一天的数据，包含多个异常事件

        Args:
            date: 日期
            anomaly_count: 异常事件数量

        Returns:
            时间序列数据（包含异常标注）
        """
        data = self.generate_realistic_day(date)

        # 随机选择异常时段
        total_minutes = 24 * 60
        anomaly_minutes = sorted(random.sample(range(0, total_minutes, 10), anomaly_count))

        for idx, start_minute in enumerate(anomaly_minutes):
            # 生成异常
            anomaly_type = random.choice(['spike', 'step', 'periodic'])

            if anomaly_type == 'spike':
                # 尖峰异常
                spike_start = date + timedelta(minutes=start_minute)
                spike_data = self.anomaly_gen.generate_spike(
                    base_cpu=40,
                    spike_cpu=95,
                    start_time=spike_start,
                    duration_seconds=300,
                    interval_seconds=60
                )
                # 标记为异常
                for metric in spike_data:
                    metric['anomaly'] = True
                    metric['anomaly_type'] = 'spike'
                    metric['anomaly_id'] = f'anomaly_{idx + 1}'

                # 替换对应时段的数据
                for i, spike_metric in enumerate(spike_data):
                    data_idx = start_minute + i
                    if data_idx < len(data):
                        data[data_idx] = spike_metric

            elif anomaly_type == 'step':
                # 阶梯异常
                step_start = date + timedelta(minutes=start_minute)
                step_data = self.anomaly_gen.generate_step_anomaly(
                    base_cpu=40,
                    anomaly_cpu=90,
                    start_time=step_start,
                    duration_minutes=10,
                    interval_seconds=60
                )
                for metric in step_data:
                    metric['anomaly'] = True
                    metric['anomaly_type'] = 'step'
                    metric['anomaly_id'] = f'anomaly_{idx + 1}'

                for i, step_metric in enumerate(step_data):
                    data_idx = start_minute + i
                    if data_idx < len(data):
                        data[data_idx] = step_metric

        return data


def save_data(data: List[Dict], output_file: str, format: str = 'json'):
    """
    保存生成的数据到文件

    Args:
        data: 数据列表
        output_file: 输出文件路径
        format: 文件格式 ('json' 或 'csv')
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == 'json':
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"数据已保存到 {output_file}")

    elif format == 'csv':
        # 展开嵌套字典
        df = pd.json_normalize(data)
        df.to_csv(output_file, index=False)
        print(f"数据已保存到 {output_file}")

    else:
        raise ValueError(f"不支持的格式: {format}")


def main():
    """主函数 - 命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Mock CPU 数据生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:

1. 生成 1 小时的正常数据:
   %(prog)s --type normal --duration 60 --output /tmp/normal_data.json

2. 生成包含异常的 24 小时数据:
   %(prog)s --type mixed --duration 1440 --anomalies 5 --output /tmp/with_anomalies.json

3. 生成 CSV 格式数据:
   %(prog)s --type normal --duration 60 --output /tmp/data.csv --format csv

4. 生成特定场景的测试数据:
   %(prog)s --type spike --base-cpu 40 --spike-cpu 95 --duration 10 --output /tmp/spike.json
        """
    )

    parser.add_argument('--type', choices=['normal', 'spike', 'step', 'periodic', 'mixed'],
                       default='normal', help='数据类型（默认: normal）')
    parser.add_argument('--duration', type=int, default=60,
                       help='持续时间（分钟，默认: 60）')
    parser.add_argument('--interval', type=int, default=1,
                       help='采样间隔（秒，默认: 1）')
    parser.add_argument('--output', type=str, required=True,
                       help='输出文件路径')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='输出格式（默认: json）')
    parser.add_argument('--seed', type=int, default=None,
                       help='随机种子（用于可重复生成）')

    # 异常相关参数
    parser.add_argument('--base-cpu', type=float, default=40.0,
                       help='基线 CPU 使用率（默认: 40）')
    parser.add_argument('--spike-cpu', type=float, default=95.0,
                       help='尖峰/异常 CPU 使用率（默认: 95）')
    parser.add_argument('--anomalies', type=int, default=3,
                       help='异常事件数量（用于 mixed 类型）')
    parser.add_argument('--period', type=int, default=5,
                       help='周期时长（分钟，用于 periodic 类型）')

    # 正常数据参数
    parser.add_argument('--avg-cpu', type=float, default=40.0,
                       help='平均 CPU 使用率（用于 normal 类型）')
    parser.add_argument('--variance', type=float, default=10.0,
                       help='CPU 波动范围（用于 normal 类型）')

    args = parser.parse_args()

    # 创建生成器
    generator = MixedScenarioGenerator(seed=args.seed)

    # 生成数据
    start_time = datetime.now().replace(microsecond=0)

    if args.type == 'normal':
        normal_gen = NormalDataGenerator(
            base_cpu=args.avg_cpu,
            variance=args.variance,
            seed=args.seed
        )
        data = normal_gen.generate_time_series(
            start_time,
            duration_minutes=args.duration,
            interval_seconds=args.interval
        )

    elif args.type == 'spike':
        anomaly_gen = AnomalyDataGenerator(seed=args.seed)
        data = anomaly_gen.generate_spike(
            base_cpu=args.base_cpu,
            spike_cpu=args.spike_cpu,
            start_time=start_time,
            duration_seconds=args.duration * 60,
            interval_seconds=args.interval
        )

    elif args.type == 'step':
        anomaly_gen = AnomalyDataGenerator(seed=args.seed)
        data = anomaly_gen.generate_step_anomaly(
            base_cpu=args.base_cpu,
            anomaly_cpu=args.spike_cpu,
            start_time=start_time,
            duration_minutes=args.duration,
            interval_seconds=args.interval
        )

    elif args.type == 'periodic':
        anomaly_gen = AnomalyDataGenerator(seed=args.seed)
        data = anomaly_gen.generate_periodic_anomaly(
            base_cpu=args.base_cpu,
            peak_cpu=args.spike_cpu,
            start_time=start_time,
            duration_minutes=args.duration,
            period_minutes=args.period,
            interval_seconds=args.interval
        )

    elif args.type == 'mixed':
        data = generator.generate_day_with_anomalies(
            start_time,
            anomaly_count=args.anomalies
        )

    else:
        print(f"错误: 不支持的数据类型 {args.type}")
        sys.exit(1)

    # 保存数据
    save_data(data, args.output, format=args.format)

    # 打印统计信息
    cpu_values = [m['cpu_percent'] for m in data]
    print(f"\n数据统计:")
    print(f"  数据点数量: {len(data)}")
    print(f"  CPU 使用率 - 最小值: {min(cpu_values):.2f}%, 最大值: {max(cpu_values):.2f}%, 平均值: {sum(cpu_values)/len(cpu_values):.2f}%")

    if 'anomaly' in data[0]:
        anomaly_count = sum(1 for m in data if m.get('anomaly', False))
        print(f"  异常数据点: {anomaly_count} ({anomaly_count/len(data)*100:.1f}%)")


if __name__ == '__main__':
    main()
