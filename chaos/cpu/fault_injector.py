#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集故障注入器 - 模拟各种数据采集异常场景

功能:
1. 模拟 /proc 文件读取失败
2. 模拟数据格式异常
3. 模拟网络超时（远程数据源）
4. 模拟权限不足
5. 模拟磁盘 I/O 错误
"""

import os
import sys
import time
import random
import argparse
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, List
import json


class FaultInjector:
    """故障注入器基类"""

    def __init__(self, fault_type: str):
        self.fault_type = fault_type
        self.original_state = {}
        self.injected = False

    def inject(self):
        """注入故障"""
        raise NotImplementedError

    def cleanup(self):
        """清理故障，恢复原始状态"""
        raise NotImplementedError


class ProcFileReadFailure(FaultInjector):
    """/proc 文件读取失败模拟器"""

    def __init__(self, proc_file: str = '/proc/stat', failure_rate: float = 1.0):
        """
        初始化 /proc 文件读取失败模拟器

        Args:
            proc_file: 要模拟失败的 /proc 文件路径
            failure_rate: 失败率 (0.0-1.0)，1.0 表示总是失败
        """
        super().__init__('proc_file_read_failure')
        self.proc_file = proc_file
        self.failure_rate = max(0.0, min(1.0, failure_rate))
        self.backup_file = None

    def inject(self):
        """注入故障：临时替换 /proc 文件"""
        if self.injected:
            print("警告: 故障已注入")
            return

        # 备份原始文件
        if os.path.exists(self.proc_file):
            self.backup_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            with open(self.proc_file, 'r') as f:
                shutil.copyfileobj(f, self.backup_file)
            self.backup_file.close()

            # 替换为可读但格式错误的文件
            os.remove(self.proc_file)

        # 创建触发读取错误的文件
        if self.failure_rate >= 1.0:
            # 创建一个空文件或特殊文件触发错误
            Path(self.proc_file).touch()
        else:
            # 创建一个有时读取成功、有时失败的文件
            with open(self.proc_file, 'w') as f:
                f.write("corrupted data for testing\n")

        self.injected = True
        print(f"[故障注入] {self.proc_file} 读取失败模拟已启动 (失败率: {self.failure_rate})")

    def cleanup(self):
        """清理故障：恢复原始 /proc 文件"""
        if not self.injected:
            return

        try:
            if self.backup_file and os.path.exists(self.backup_file.name):
                # 恢复原始文件
                shutil.copy(self.backup_file.name, self.proc_file)
                os.unlink(self.backup_file.name)
                print(f"[清理] {self.proc_file} 已恢复")
        except Exception as e:
            print(f"[警告] 清理失败: {e}")
            print("[提示] 可能需要手动恢复或重启系统")

        self.injected = False


class DataFormatCorruption(FaultInjector):
    """数据格式损坏模拟器"""

    def __init__(self, proc_file: str = '/proc/stat', corruption_type: str = 'invalid_format'):
        """
        初始化数据格式损坏模拟器

        Args:
            proc_file: 目标 /proc 文件
            corruption_type: 损坏类型
                - 'invalid_format': 无效格式
                - 'missing_fields': 缺少字段
                - 'wrong_types': 错误的数据类型
                - 'inconsistent_data': 不一致的数据
        """
        super().__init__('data_format_corruption')
        self.proc_file = proc_file
        self.corruption_type = corruption_type
        self.backup_file = None

    def _generate_corrupted_data(self) -> str:
        """生成损坏的数据"""
        if self.corruption_type == 'invalid_format':
            return "cpu  bad_data totally_wrong format!!!\n"

        elif self.corruption_type == 'missing_fields':
            return "cpu 100 200\n"  # 缺少大部分字段

        elif self.corruption_type == 'wrong_types':
            return "cpu one two three four five\n"

        elif self.corruption_type == 'inconsistent_data':
            return """cpu 100 200 300 400 500 600 700 800 900 1000
cpu0 50 50 50 50 50 50 50 50 50 50
cpu1 total garbage data here
"""

        else:
            return "corrupted data\n"

    def inject(self):
        """注入数据格式损坏"""
        if self.injected:
            return

        # 备份原始文件
        if os.path.exists(self.proc_file):
            self.backup_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            with open(self.proc_file, 'r') as f:
                shutil.copyfileobj(f, self.backup_file)
            self.backup_file.close()

            # 替换为损坏的数据
            with open(self.proc_file, 'w') as f:
                f.write(self._generate_corrupted_data())

        self.injected = True
        print(f"[故障注入] {self.proc_file} 数据格式已损坏 (类型: {self.corruption_type})")

    def cleanup(self):
        """清理：恢复原始文件"""
        if not self.injected:
            return

        try:
            if self.backup_file and os.path.exists(self.backup_file.name):
                shutil.copy(self.backup_file.name, self.proc_file)
                os.unlink(self.backup_file.name)
                print(f"[清理] {self.proc_file} 已恢复")
        except Exception as e:
            print(f"[警告] 清理失败: {e}")

        self.injected = False


class NetworkTimeoutSimulator:
    """网络超时模拟器（用于远程数据源）"""

    def __init__(self, host: str = 'localhost', port: int = 9090,
                 timeout: float = 5.0, response_delay: float = 30.0):
        """
        初始化网络超时模拟器

        Args:
            host: 监听地址
            port: 监听端口
            timeout: 服务器超时设置
            response_delay: 响应延迟（秒），大于 timeout 则触发超时
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.response_delay = response_delay
        self.running = False

    def _delayed_response_server(self):
        """延迟响应服务器"""
        import socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        server_socket.settimeout(self.timeout)

        print(f"[超时模拟器] 服务器启动于 {self.host}:{self.port}")
        print(f"  服务器超时: {self.timeout}秒")
        print(f"  响应延迟: {self.response_delay}秒")

        self.running = True

        try:
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    print(f"[连接] 来自 {address}")

                    # 等待超过超时时间
                    time.sleep(self.response_delay)

                    # 发送响应（太晚了）
                    response = b"HTTP/1.1 200 OK\r\n\r\nDelayed response"
                    try:
                        client_socket.send(response)
                    except:
                        pass  # 客户端可能已经断开

                    client_socket.close()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[错误] {e}")
        finally:
            server_socket.close()

    def inject(self):
        """启动延迟服务器"""
        import threading
        server_thread = threading.Thread(target=self._delayed_response_server)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(1)  # 等待服务器启动

    def cleanup(self):
        """停止服务器"""
        self.running = False
        print("[清理] 网络超时模拟器已停止")


class PermissionDeniedSimulator(FaultInjector):
    """权限不足模拟器"""

    def __init__(self, path: str = '/proc/cpuinfo'):
        """
        初始化权限不足模拟器

        Args:
            path: 要限制访问的路径
        """
        super().__init__('permission_denied')
        self.path = path
        self.original_mode = None

    def inject(self):
        """注入权限不足"""
        if self.injected:
            return

        if os.path.exists(self.path):
            # 保存原始权限
            stat_info = os.stat(self.path)
            self.original_mode = stat_info.st_mode

            # 修改权限为仅 root 可读
            try:
                os.chmod(self.path, 0o600)
                self.injected = True
                print(f"[故障注入] {self.path} 权限已限制 (需要 root 访问)")
            except Exception as e:
                print(f"[错误] 无法修改权限: {e}")
                print("[提示] 此操作需要 root 权限")
        else:
            print(f"[错误] 路径不存在: {self.path}")

    def cleanup(self):
        """恢复原始权限"""
        if not self.injected:
            return

        try:
            if self.original_mode is not None and os.path.exists(self.path):
                os.chmod(self.path, self.original_mode)
                print(f"[清理] {self.path} 权限已恢复")
        except Exception as e:
            print(f"[警告] 清理失败: {e}")
            print("[提示] 可能需要手动恢复权限")

        self.injected = False


class DiskIOFailureSimulator(FaultInjector):
    """磁盘 I/O 失败模拟器"""

    def __init__(self, data_dir: str):
        """
        初始化磁盘 I/O 失败模拟器

        Args:
            data_dir: 数据存储目录
        """
        super().__init__('disk_io_failure')
        self.data_dir = data_dir
        self.original_dir = None

    def inject(self):
        """注入磁盘 I/O 失败：填满磁盘空间"""
        if self.injected:
            return

        # 创建临时大文件填满磁盘
        try:
            # 检查可用空间
            stat = os.statvfs(self.data_dir)
            available_space = stat.f_bavail * stat.f_frsize

            # 创建一个占用剩余空间的文件
            self.original_dir = tempfile.mkdtemp(prefix='disk_fill_')
            big_file = os.path.join(self.original_dir, 'big_file.dat')

            # 逐步填充，留 100MB
            file_size = available_space - (100 * 1024 * 1024)

            print(f"[故障注入] 正在填充磁盘空间...")
            print(f"  目标目录: {self.data_dir}")
            print(f"  文件大小: {file_size / (1024**3):.2f} GB")

            # 使用 dd 命令填充（更快）
            os.system(f"dd if=/dev/zero of={big_file} bs=1M count="
                     f"{file_size // (1024*1024)} 2>/dev/null")

            self.injected = True
            print(f"[故障注入] 磁盘 I/O 失败已模拟（磁盘空间不足）")

        except Exception as e:
            print(f"[错误] 磁盘填充失败: {e}")

    def cleanup(self):
        """清理：删除大文件释放空间"""
        if not self.injected:
            return

        try:
            if self.original_dir and os.path.exists(self.original_dir):
                shutil.rmtree(self.original_dir)
                print(f"[清理] 磁盘空间已释放")
        except Exception as e:
            print(f"[警告] 清理失败: {e}")
            print(f"[提示] 手动删除: {self.original_dir}")

        self.injected = False


class RandomFaultInjector:
    """随机故障注入器 - 组合多种故障"""

    def __init__(self, fault_config: Dict):
        """
        初始化随机故障注入器

        Args:
            fault_config: 故障配置字典
                {
                    'proc_file_failure': {'enabled': True, 'rate': 0.1},
                    'data_corruption': {'enabled': True, 'types': ['invalid_format']},
                    'permission_denied': {'enabled': False},
                    'network_timeout': {'enabled': True, 'delay': 30.0}
                }
        """
        self.fault_config = fault_config
        self.active_injectors = []

    def inject_all(self):
        """注入所有启用的故障"""
        print("[随机故障注入] 开始注入故障...")

        if self.fault_config.get('proc_file_failure', {}).get('enabled', False):
            rate = self.fault_config['proc_file_failure'].get('rate', 0.5)
            injector = ProcFileReadFailure(failure_rate=rate)
            injector.inject()
            self.active_injectors.append(injector)

        if self.fault_config.get('data_corruption', {}).get('enabled', False):
            types = self.fault_config['data_corruption'].get('types', ['invalid_format'])
            for corruption_type in types:
                injector = DataFormatCorruption(corruption_type=corruption_type)
                injector.inject()
                self.active_injectors.append(injector)

        if self.fault_config.get('permission_denied', {}).get('enabled', False):
            injector = PermissionDeniedSimulator()
            injector.inject()
            self.active_injectors.append(injector)

        if self.fault_config.get('network_timeout', {}).get('enabled', False):
            delay = self.fault_config['network_timeout'].get('delay', 30.0)
            injector = NetworkTimeoutSimulator(response_delay=delay)
            injector.inject()
            self.active_injectors.append(injector)

        print(f"[随机故障注入] 已注入 {len(self.active_injectors)} 个故障")

    def cleanup_all(self):
        """清理所有故障"""
        print("[随机故障注入] 清理所有故障...")
        for injector in self.active_injectors:
            injector.cleanup()
        self.active_injectors.clear()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='数据采集故障注入器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:

1. 模拟 /proc/stat 读取失败（100% 失败率）:
   %(prog)s --proc-failure --file /proc/stat --rate 1.0

2. 模拟数据格式损坏:
   %(prog)s --corruption --type invalid_format --file /proc/stat

3. 模拟权限不足:
   %(prog)s --permission --file /proc/cpuinfo

4. 模拟网络超时:
   %(prog)s --network-timeout --delay 30

5. 使用配置文件注入多个故障:
   %(prog)s --config fault_config.json
        """
    )

    parser.add_argument('--proc-failure', action='store_true',
                       help='模拟 /proc 文件读取失败')
    parser.add_argument('--file', default='/proc/stat',
                       help='目标文件路径（默认: /proc/stat）')
    parser.add_argument('--rate', type=float, default=1.0,
                       help='读取失败率 (0.0-1.0，默认: 1.0)')

    parser.add_argument('--corruption', action='store_true',
                       help='模拟数据格式损坏')
    parser.add_argument('--type', default='invalid_format',
                       choices=['invalid_format', 'missing_fields',
                               'wrong_types', 'inconsistent_data'],
                       help='损坏类型（默认: invalid_format）')

    parser.add_argument('--permission', action='store_true',
                       help='模拟权限不足')

    parser.add_argument('--network-timeout', action='store_true',
                       help='模拟网络超时')
    parser.add_argument('--delay', type=float, default=30.0,
                       help='响应延迟（秒，默认: 30）')

    parser.add_argument('--disk-failure', action='store_true',
                       help='模拟磁盘空间不足')
    parser.add_argument('--data-dir', default='/tmp/aiops_data',
                       help='数据目录（默认: /tmp/aiops_data）')

    parser.add_argument('--config', type=str,
                       help='故障配置 JSON 文件')

    parser.add_argument('--duration', type=int, default=60,
                       help='故障持续时间（秒，默认: 60）')

    args = parser.parse_args()

    injectors = []

    try:
        if args.config:
            # 从配置文件加载
            with open(args.config, 'r') as f:
                config = json.load(f)
            injector = RandomFaultInjector(config)
            injector.inject_all()
            injectors.append(injector)

        else:
            # 根据命令行参数创建注入器
            if args.proc_failure:
                injector = ProcFileReadFailure(args.file, args.rate)
                injector.inject()
                injectors.append(injector)

            if args.corruption:
                injector = DataFormatCorruption(args.file, args.type)
                injector.inject()
                injectors.append(injector)

            if args.permission:
                injector = PermissionDeniedSimulator(args.file)
                injector.inject()
                injectors.append(injector)

            if args.network_timeout:
                injector = NetworkTimeoutSimulator(response_delay=args.delay)
                injector.inject()
                injectors.append(injector)

            if args.disk_failure:
                injector = DiskIOFailureSimulator(args.data_dir)
                injector.inject()
                injectors.append(injector)

        if not injectors:
            print("错误: 未指定任何故障类型")
            parser.print_help()
            sys.exit(1)

        print(f"\n故障注入器运行中，持续 {args.duration} 秒...")
        print("按 Ctrl+C 提前停止")

        time.sleep(args.duration)

    except KeyboardInterrupt:
        print("\n收到停止信号，正在清理...")
    finally:
        print("\n清理故障注入...")
        for injector in injectors:
            if hasattr(injector, 'cleanup_all'):
                injector.cleanup_all()
            else:
                injector.cleanup()

        print("故障注入器已停止")


if __name__ == '__main__':
    main()
