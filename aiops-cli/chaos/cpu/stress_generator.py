#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU 压力生成器 - 混沌工程/故障注入工具

功能:
1. 生成指定 CPU 使用率的高负载
2. 模拟单核过载
3. 模拟多进程 CPU 争用
4. 生成间歇性 CPU 尖峰
"""

import os
import sys
import time
import signal
import argparse
import multiprocessing
import random
import math
from datetime import datetime, timedelta
from typing import Optional, List


class CPUStressGenerator:
    """CPU 压力生成器基类"""

    def __init__(self, load_percent: float, duration: int, core_id: Optional[int] = None):
        """
        初始化 CPU 压力生成器

        Args:
            load_percent: 目标 CPU 使用率 (0-100)
            duration: 持续时间（秒）
            core_id: 绑定的 CPU 核心编号，None 表示不绑定
        """
        self.load_percent = max(0, min(100, load_percent))
        self.duration = duration
        self.core_id = core_id
        self.running = False
        self.processes: List[multiprocessing.Process] = []

    def _calculate_sleep_time(self, work_time: float) -> float:
        """
        根据目标 CPU 使用率计算休眠时间

        Args:
            work_time: 工作时间（秒）

        Returns:
            休眠时间（秒）
        """
        if self.load_percent >= 100:
            return 0
        if self.load_percent <= 0:
            return 1.0

        # 公式: work_time / (work_time + sleep_time) = load_percent / 100
        # sleep_time = work_time * (100 / load_percent - 1)
        return work_time * (100 / self.load_percent - 1)

    def _stress_worker(self):
        """CPU 压力工作进程"""
        # 设置 CPU 亲和性
        if self.core_id is not None:
            try:
                pid = os.getpid()
                # 使用 taskset 命令设置 CPU 亲和性
                os.system(f"taskset -p -c {self.core_id} {pid} > /dev/null 2>&1")
            except Exception as e:
                print(f"警告: 无法设置 CPU 亲和性: {e}")

        # 计算工作/休眠周期
        cycle_time = 0.1  # 100ms 一个周期
        work_time = cycle_time * (self.load_percent / 100)
        sleep_time = self._calculate_sleep_time(work_time)

        end_time = time.time() + self.duration

        while time.time() < end_time:
            # CPU 密集型工作
            start = time.time()
            while time.time() - start < work_time:
                # 执行一些无意义的计算
                _ = sum(math.sqrt(i) for i in range(1000))

            # 休眠以控制 CPU 使用率
            if sleep_time > 0:
                time.sleep(sleep_time)

    def start(self):
        """启动 CPU 压力生成"""
        if self.running:
            print("警告: 压力生成器已在运行")
            return

        self.running = True
        self.processes = []

        # 为每个需要绑定的核心启动一个进程
        cores = [self.core_id] if self.core_id is not None else [None]
        for core in cores:
            p = multiprocessing.Process(target=self._stress_worker)
            p.start()
            self.processes.append(p)

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
              f"CPU 压力生成器已启动")
        print(f"  目标 CPU 使用率: {self.load_percent}%")
        print(f"  持续时间: {self.duration}秒")
        if self.core_id is not None:
            print(f"  绑定核心: CPU {self.core_id}")
        print(f"  进程 PID: {[p.pid for p in self.processes]}")

    def stop(self):
        """停止 CPU 压力生成"""
        if not self.running:
            return

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
              f"停止 CPU 压力生成器...")

        for p in self.processes:
            if p.is_alive():
                p.terminate()
                p.join(timeout=5)
                if p.is_alive():
                    p.kill()

        self.running = False
        self.processes.clear()
        print("CPU 压力生成器已停止")

    def wait(self):
        """等待所有进程完成"""
        for p in self.processes:
            p.join()


class MultiCoreStressGenerator(CPUStressGenerator):
    """多核 CPU 压力生成器"""

    def __init__(self, load_percent: float, duration: int, core_ids: List[int]):
        """
        初始化多核压力生成器

        Args:
            load_percent: 每个核心的目标 CPU 使用率
            duration: 持续时间（秒）
            core_ids: 要过载的核心列表
        """
        super().__init__(load_percent, duration)
        self.core_ids = core_ids

    def start(self):
        """在指定核心上启动压力生成"""
        if self.running:
            print("警告: 压力生成器已在运行")
            return

        self.running = True
        self.processes = []

        for core_id in self.core_ids:
            p = multiprocessing.Process(target=self._stress_worker_per_core, args=(core_id,))
            p.start()
            self.processes.append(p)

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
              f"多核 CPU 压力生成器已启动")
        print(f"  目标 CPU 使用率: {self.load_percent}%")
        print(f"  持续时间: {self.duration}秒")
        print(f"  绑定核心: {self.core_ids}")
        print(f"  进程 PID: {[p.pid for p in self.processes]}")

    def _stress_worker_per_core(self, core_id: int):
        """在指定核心上执行压力测试"""
        # 设置 CPU 亲和性
        try:
            pid = os.getpid()
            os.system(f"taskset -p -c {core_id} {pid} > /dev/null 2>&1")
        except Exception as e:
            print(f"警告: 无法设置 CPU 亲和性: {e}")

        # CPU 压力循环
        cycle_time = 0.1
        work_time = cycle_time * (self.load_percent / 100)
        sleep_time = self._calculate_sleep_time(work_time)

        end_time = time.time() + self.duration

        while time.time() < end_time:
            start = time.time()
            while time.time() - start < work_time:
                _ = sum(math.sqrt(i) for i in range(1000))

            if sleep_time > 0:
                time.sleep(sleep_time)


class IntermittentStressGenerator:
    """间歇性 CPU 尖峰生成器"""

    def __init__(self, peak_load: float, baseline_load: float,
                 peak_duration: int, baseline_duration: int,
                 total_duration: int):
        """
        初始化间歇性尖峰生成器

        Args:
            peak_load: 尖峰时 CPU 使用率
            baseline_load: 基线 CPU 使用率
            peak_duration: 每次尖峰持续时间（秒）
            baseline_duration: 基线持续时间（秒）
            total_duration: 总持续时间（秒）
        """
        self.peak_load = peak_load
        self.baseline_load = baseline_load
        self.peak_duration = peak_duration
        self.baseline_duration = baseline_duration
        self.total_duration = total_duration
        self.running = False
        self.processes: List[multiprocessing.Process] = []

    def start(self):
        """启动间歇性压力生成"""
        if self.running:
            print("警告: 压力生成器已在运行")
            return

        self.running = True
        end_time = time.time() + self.total_duration

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
              f"间歇性 CPU 尖峰生成器已启动")
        print(f"  尖峰负载: {self.peak_load}%")
        print(f"  基线负载: {self.baseline_load}%")
        print(f"  尖峰持续时间: {self.peak_duration}秒")
        print(f"  基线持续时间: {self.baseline_duration}秒")
        print(f"  总持续时间: {self.total_duration}秒")

        cycle_count = 0
        while time.time() < end_time:
            cycle_count += 1
            print(f"\n[周期 {cycle_count}] 开始基线阶段...")

            # 基线阶段
            baseline_gen = CPUStressGenerator(
                self.baseline_load,
                self.baseline_duration
            )
            baseline_gen.start()
            baseline_gen.wait()

            if time.time() >= end_time:
                break

            print(f"\n[周期 {cycle_count}] 开始尖峰阶段...")

            # 尖峰阶段
            peak_gen = CPUStressGenerator(
                self.peak_load,
                min(self.peak_duration, int(end_time - time.time()))
            )
            peak_gen.start()
            peak_gen.wait()

        self.running = False
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
              f"间歇性 CPU 尖峰生成器已完成")


class ProcessContentionSimulator:
    """进程 CPU 争用模拟器"""

    def __init__(self, num_processes: int, load_per_process: float, duration: int):
        """
        初始化进程争用模拟器

        Args:
            num_processes: 进程数量
            load_per_process: 每个进程的 CPU 使用率
            duration: 持续时间（秒）
        """
        self.num_processes = num_processes
        self.load_per_process = load_per_process
        self.duration = duration
        self.running = False
        self.processes: List[multiprocessing.Process] = []

    def _contention_worker(self, worker_id: int):
        """单个争用进程"""
        print(f"工作进程 {worker_id} (PID {os.getpid()}) 已启动")

        cycle_time = 0.1
        work_time = cycle_time * (self.load_per_process / 100)

        # 计算休眠时间以达到目标 CPU 使用率
        if self.load_per_process >= 100:
            sleep_time = 0
        elif self.load_per_process <= 0:
            sleep_time = 1.0
        else:
            sleep_time = work_time * (100 / self.load_per_process - 1)

        end_time = time.time() + self.duration

        while time.time() < end_time:
            start = time.time()
            while time.time() - start < work_time:
                # 模拟复杂计算
                _ = sum(math.sqrt(i) for i in range(1000))

            if sleep_time > 0:
                time.sleep(sleep_time)

    def start(self):
        """启动进程争用模拟"""
        if self.running:
            print("警告: 争用模拟器已在运行")
            return

        self.running = True
        self.processes.clear()

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
              f"进程 CPU 争用模拟器已启动")
        print(f"  进程数量: {self.num_processes}")
        print(f"  每进程目标 CPU: {self.load_per_process}%")
        print(f"  持续时间: {self.duration}秒")

        for i in range(self.num_processes):
            p = multiprocessing.Process(target=self._contention_worker, args=(i,))
            p.start()
            self.processes.append(p)

        print(f"  已启动进程 PIDs: {[p.pid for p in self.processes]}")

    def stop(self):
        """停止所有争用进程"""
        if not self.running:
            return

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
              f"停止进程争用模拟器...")

        for p in self.processes:
            if p.is_alive():
                p.terminate()
                p.join(timeout=5)
                if p.is_alive():
                    p.kill()

        self.running = False
        self.processes.clear()
        print("进程争用模拟器已停止")

    def wait(self):
        """等待所有进程完成"""
        for p in self.processes:
            p.join()


def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(
        description='CPU 压力生成器 - 混沌工程测试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:

1. 生成 95% CPU 负载，持续 300 秒:
   %(prog)s --load 95 --duration 300

2. 在 CPU 核心 0 上生成 100% 负载（单核过载）:
   %(prog)s --load 100 --duration 300 --core 0

3. 在核心 0 和 1 上生成高负载:
   %(prog)s --load 90 --duration 300 --multi-core 0 1

4. 模拟进程 CPU 争用（10个进程，每进程 20%）:
   %(prog)s --contention --num-processes 10 --load-per-process 20 --duration 300

5. 生成间歇性 CPU 尖峰（95% 尖峰，20% 基线）:
   %(prog)s --intermittent --peak-load 95 --baseline-load 20 --peak-duration 30 --baseline-duration 60 --total-duration 300
        """
    )

    parser.add_argument('--load', type=float, default=95,
                       help='目标 CPU 使用率 (0-100, 默认: 95)')
    parser.add_argument('--duration', type=int, default=300,
                       help='持续时间（秒，默认: 300）')
    parser.add_argument('--core', type=int, default=None,
                       help='绑定的 CPU 核心编号（用于单核过载测试）')

    # 多核过载选项
    parser.add_argument('--multi-core', nargs='+', type=int, metavar='CORE_ID',
                       help='多个核心编号（例如: --multi-core 0 1 2）')

    # 进程争用选项
    parser.add_argument('--contention', action='store_true',
                       help='启用进程争用模拟模式')
    parser.add_argument('--num-processes', type=int, default=10,
                       help='争用进程数量（默认: 10）')
    parser.add_argument('--load-per-process', type=float, default=20,
                       help='每个进程的 CPU 使用率（默认: 20%%）')

    # 间歇性尖峰选项
    parser.add_argument('--intermittent', action='store_true',
                       help='启用间歇性尖峰模式')
    parser.add_argument('--peak-load', type=float, default=95,
                       help='尖峰时 CPU 使用率（默认: 95）')
    parser.add_argument('--baseline-load', type=float, default=20,
                       help='基线 CPU 使用率（默认: 20）')
    parser.add_argument('--peak-duration', type=int, default=30,
                       help='每次尖峰持续时间（秒，默认: 30）')
    parser.add_argument('--baseline-duration', type=int, default=60,
                       help='基线持续时间（秒，默认: 60）')
    parser.add_argument('--total-duration', type=int, default=300,
                       help='总持续时间（秒，默认: 300）')

    args = parser.parse_args()

    # 验证参数
    if args.load < 0 or args.load > 100:
        print("错误: CPU 使用率必须在 0-100 之间")
        sys.exit(1)

    if args.contention:
        # 进程争用模式
        simulator = ProcessContentionSimulator(
            args.num_processes,
            args.load_per_process,
            args.duration
        )
        simulator.start()

        # 注册信号处理
        def signal_handler(signum, frame):
            print("\n收到停止信号，正在清理...")
            simulator.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print(f"\n模拟器运行中，按 Ctrl+C 停止...")
        simulator.wait()

    elif args.intermittent:
        # 间歇性尖峰模式
        generator = IntermittentStressGenerator(
            args.peak_load,
            args.baseline_load,
            args.peak_duration,
            args.baseline_duration,
            args.total_duration
        )
        generator.start()

    elif args.multi_core:
        # 多核过载模式
        generator = MultiCoreStressGenerator(
            args.load,
            args.duration,
            args.multi_core
        )
        generator.start()

        # 注册信号处理
        def signal_handler(signum, frame):
            print("\n收到停止信号，正在清理...")
            generator.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print(f"\n模拟器运行中，按 Ctrl+C 停止...")
        generator.wait()

    else:
        # 标准模式
        generator = CPUStressGenerator(
            args.load,
            args.duration,
            args.core
        )
        generator.start()

        # 注册信号处理
        def signal_handler(signum, frame):
            print("\n收到停止信号，正在清理...")
            generator.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print(f"\n模拟器运行中，按 Ctrl+C 停止...")
        generator.wait()


if __name__ == '__main__':
    main()
