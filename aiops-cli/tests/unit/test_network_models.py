#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network 数据采集器和模型单元测试

测试内容:
1. Network 数据模型
2. Connection 数据模型
3. Network 数据采集
4. Connection 数据采集
"""

import pytest
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from aiops.network.models import NetworkMetric, ConnectionMetric


class TestNetworkMetric:
    """Network 指标模型测试"""

    def test_network_metric_creation(self):
        """测试 Network 指标对象创建"""
        timestamp = datetime.now()
        metric = NetworkMetric(
            timestamp=timestamp,
            interface="eth0",
            bytes_recv=1000000,
            packets_recv=1000,
            errin=0,
            dropin=0,
            bytes_sent=500000,
            packets_sent=500,
            errout=0,
            dropout=0,
            is_up=True,
            speed_mbps=1000,
            mtu=1500,
        )

        assert metric.interface == "eth0"
        assert metric.bytes_recv == 1000000
        assert metric.bytes_sent == 500000
        assert metric.is_up is True

    def test_network_metric_properties(self):
        """测试 Network 指标属性计算"""
        metric = NetworkMetric(
            timestamp=datetime.now(),
            interface="eth0",
            bytes_recv=1048576,  # 1 MB
            packets_recv=1000,
            errin=10,
            dropin=5,
            bytes_sent=2097152,  # 2 MB
            packets_sent=2000,
            errout=20,
            dropout=10,
            is_up=True,
            speed_mbps=1000,
            mtu=1500,
        )

        # Test total_bytes
        assert metric.total_bytes == 1048576 + 2097152

        # Test total_packets
        assert metric.total_packets == 3000

        # Test total_errors
        assert metric.total_errors == 30

        # Test total_drops
        assert metric.total_drops == 15

        # Test bytes_recv_mb
        assert metric.bytes_recv_mb == pytest.approx(1.0, abs=0.01)

        # Test bytes_sent_mb
        assert metric.bytes_sent_mb == pytest.approx(2.0, abs=0.01)

        # Test total_bytes_mb
        assert metric.total_bytes_mb == pytest.approx(3.0, abs=0.01)

        # Test error_rate_recv
        assert metric.error_rate_recv == pytest.approx(0.01, abs=0.001)

        # Test error_rate_sent
        assert metric.error_rate_sent == pytest.approx(0.01, abs=0.001)

        # Test drop_rate_recv
        assert metric.drop_rate_recv == pytest.approx(0.005, abs=0.001)

        # Test drop_rate_sent
        assert metric.drop_rate_sent == pytest.approx(0.005, abs=0.001)

    def test_network_metric_validation(self):
        """测试 Network 指标验证"""
        # Test empty interface name
        with pytest.raises(ValueError):
            NetworkMetric(
                timestamp=datetime.now(),
                interface="",
                bytes_recv=0,
                packets_recv=0,
                errin=0,
                dropin=0,
                bytes_sent=0,
                packets_sent=0,
                errout=0,
                dropout=0,
            )

        # Test negative bytes_recv
        with pytest.raises(ValueError):
            NetworkMetric(
                timestamp=datetime.now(),
                interface="eth0",
                bytes_recv=-1,
                packets_recv=0,
                errin=0,
                dropin=0,
                bytes_sent=0,
                packets_sent=0,
                errout=0,
                dropout=0,
            )

        # Test negative bytes_sent
        with pytest.raises(ValueError):
            NetworkMetric(
                timestamp=datetime.now(),
                interface="eth0",
                bytes_recv=0,
                packets_recv=0,
                errin=0,
                dropin=0,
                bytes_sent=-1,
                packets_sent=0,
                errout=0,
                dropout=0,
            )

    def test_network_metric_to_dict(self):
        """测试 Network 指标转换为字典"""
        timestamp = datetime.now()
        metric = NetworkMetric(
            timestamp=timestamp,
            interface="eth0",
            bytes_recv=1000000,
            packets_recv=1000,
            errin=0,
            dropin=0,
            bytes_sent=500000,
            packets_sent=500,
            errout=0,
            dropout=0,
            is_up=True,
            speed_mbps=1000,
            mtu=1500,
        )

        metric_dict = metric.to_dict()
        assert metric_dict['interface'] == "eth0"
        assert metric_dict['bytes_recv'] == 1000000
        assert metric_dict['bytes_sent'] == 500000
        assert 'total_bytes' in metric_dict
        assert 'total_packets' in metric_dict


class TestConnectionMetric:
    """Connection 指标模型测试"""

    def test_connection_metric_creation(self):
        """测试 Connection 指标对象创建"""
        timestamp = datetime.now()
        metric = ConnectionMetric(
            timestamp=timestamp,
            protocol="tcp",
            local_address="192.168.1.100",
            local_port=8080,
            remote_address="192.168.1.101",
            remote_port=52341,
            status="ESTABLISHED",
            pid=1234,
            process_name="nginx",
            fd=10,
            family="AF_INET",
        )

        assert metric.protocol == "tcp"
        assert metric.local_port == 8080
        assert metric.remote_port == 52341
        assert metric.status == "ESTABLISHED"
        assert metric.pid == 1234

    def test_connection_metric_properties(self):
        """测试 Connection 指标属性计算"""
        metric = ConnectionMetric(
            timestamp=datetime.now(),
            protocol="tcp",
            local_address="192.168.1.100",
            local_port=8080,
            remote_address="192.168.1.101",
            remote_port=52341,
            status="ESTABLISHED",
            pid=1234,
            process_name="nginx",
        )

        # Test is_established
        assert metric.is_established is True
        assert metric.is_listening is False
        assert metric.is_time_wait is False
        assert metric.is_close_wait is False

        # Test endpoints
        assert metric.local_endpoint == "192.168.1.100:8080"
        assert metric.remote_endpoint == "192.168.1.101:52341"
        assert metric.connection_tuple == "192.168.1.100:8080 -> 192.168.1.101:52341"

        # Test is_ipv6
        assert metric.is_ipv6 is False

    def test_connection_metric_listening(self):
        """测试 LISTEN 状态连接"""
        metric = ConnectionMetric(
            timestamp=datetime.now(),
            protocol="tcp",
            local_address="0.0.0.0",
            local_port=80,
            remote_address="0.0.0.0",
            remote_port=0,
            status="LISTEN",
            pid=1234,
            process_name="nginx",
        )

        assert metric.is_listening is True
        assert metric.is_established is False

    def test_connection_metric_time_wait(self):
        """测试 TIME_WAIT 状态连接"""
        metric = ConnectionMetric(
            timestamp=datetime.now(),
            protocol="tcp",
            local_address="192.168.1.100",
            local_port=8080,
            remote_address="192.168.1.101",
            remote_port=52341,
            status="TIME_WAIT",
        )

        assert metric.is_time_wait is True
        assert metric.is_established is False

    def test_connection_metric_close_wait(self):
        """测试 CLOSE_WAIT 状态连接"""
        metric = ConnectionMetric(
            timestamp=datetime.now(),
            protocol="tcp",
            local_address="192.168.1.100",
            local_port=8080,
            remote_address="192.168.1.101",
            remote_port=52341,
            status="CLOSE_WAIT",
        )

        assert metric.is_close_wait is True
        assert metric.is_established is False

    def test_connection_metric_validation(self):
        """测试 Connection 指标验证"""
        # Test invalid protocol
        with pytest.raises(ValueError):
            ConnectionMetric(
                timestamp=datetime.now(),
                protocol="invalid",
                local_address="192.168.1.100",
                local_port=8080,
                remote_address="192.168.1.101",
                remote_port=52341,
                status="ESTABLISHED",
            )

        # Test invalid local_port
        with pytest.raises(ValueError):
            ConnectionMetric(
                timestamp=datetime.now(),
                protocol="tcp",
                local_address="192.168.1.100",
                local_port=-1,
                remote_address="192.168.1.101",
                remote_port=52341,
                status="ESTABLISHED",
            )

        # Test invalid remote_port
        with pytest.raises(ValueError):
            ConnectionMetric(
                timestamp=datetime.now(),
                protocol="tcp",
                local_address="192.168.1.100",
                local_port=8080,
                remote_address="192.168.1.101",
                remote_port=70000,
                status="ESTABLISHED",
            )

        # Test invalid TCP status
        with pytest.raises(ValueError):
            ConnectionMetric(
                timestamp=datetime.now(),
                protocol="tcp",
                local_address="192.168.1.100",
                local_port=8080,
                remote_address="192.168.1.101",
                remote_port=52341,
                status="INVALID_STATUS",
            )

    def test_connection_metric_ipv6(self):
        """测试 IPv6 连接"""
        metric = ConnectionMetric(
            timestamp=datetime.now(),
            protocol="tcp6",
            local_address="::1",
            local_port=8080,
            remote_address="::1",
            remote_port=52341,
            status="ESTABLISHED",
            family="AF_INET6",
        )

        assert metric.is_ipv6 is True

    def test_connection_metric_to_dict(self):
        """测试 Connection 指标转换为字典"""
        timestamp = datetime.now()
        metric = ConnectionMetric(
            timestamp=timestamp,
            protocol="tcp",
            local_address="192.168.1.100",
            local_port=8080,
            remote_address="192.168.1.101",
            remote_port=52341,
            status="ESTABLISHED",
            pid=1234,
            process_name="nginx",
        )

        metric_dict = metric.to_dict()
        assert metric_dict['protocol'] == "tcp"
        assert metric_dict['local_port'] == 8080
        assert metric_dict['remote_port'] == 52341
        assert metric_dict['status'] == "ESTABLISHED"
        assert 'is_established' in metric_dict
        assert 'local_endpoint' in metric_dict
        assert 'remote_endpoint' in metric_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
