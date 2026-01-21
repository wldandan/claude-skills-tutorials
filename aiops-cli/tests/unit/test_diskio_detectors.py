#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Disk I/O anomaly detectors unit tests

测试内容:
1. IO Latency Detector
2. Throughput Anomaly Detector
3. Queue Depth Detector
"""

import pytest
from datetime import datetime, timedelta
from aiops.diskio.models import DiskIOMetric
from aiops.diskio.detectors import (
    IOLatencyDetector,
    ThroughputAnomalyDetector,
    QueueDepthDetector,
)


class TestIOLatencyDetector:
    """IO latency anomaly detector tests"""

    def test_latency_detector_creation(self):
        """Test detector creation"""
        detector = IOLatencyDetector(
            latency_threshold_ms=100.0,
            spike_multiplier=3.0,
            min_samples=10,
            confidence_threshold=0.7,
        )
        assert detector.latency_threshold_ms == 100.0
        assert detector.spike_multiplier == 3.0

    def test_detect_read_latency_spike(self):
        """Test detection of read latency spike"""
        # Create metrics with normal latency
        base_time = datetime.now()
        metrics = []

        # Normal latency (10ms)
        for i in range(20):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=i),
                    device="sda",
                    reads_completed=1000 + i * 10,
                    reads_merged=0,
                    sectors_read=20000 + i * 200,
                    time_reading_ms=10000 + i * 100,  # 10ms avg
                    writes_completed=500,
                    writes_merged=0,
                    sectors_written=10000,
                    time_writing_ms=5000,
                    io_in_progress=1,
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        # Add spike (200ms)
        for i in range(5):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=20 + i),
                    device="sda",
                    reads_completed=1200 + i * 10,
                    reads_merged=0,
                    sectors_read=24000 + i * 200,
                    time_reading_ms=240000 + i * 2000,  # 200ms avg
                    writes_completed=500,
                    writes_merged=0,
                    sectors_written=10000,
                    time_writing_ms=5000,
                    io_in_progress=1,
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        detector = IOLatencyDetector(
            latency_threshold_ms=100.0, min_samples=10, confidence_threshold=0.6
        )
        anomalies = detector.detect(metrics)

        assert len(anomalies) > 0
        assert any("read" in a.type for a in anomalies)
        assert any(a.severity in ["warning", "critical"] for a in anomalies)

    def test_detect_write_latency_spike(self):
        """Test detection of write latency spike"""
        base_time = datetime.now()
        metrics = []

        # Normal write latency (5ms)
        for i in range(20):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=i),
                    device="sda",
                    reads_completed=1000,
                    reads_merged=0,
                    sectors_read=20000,
                    time_reading_ms=10000,
                    writes_completed=500 + i * 10,
                    writes_merged=0,
                    sectors_written=10000 + i * 200,
                    time_writing_ms=2500 + i * 50,  # 5ms avg
                    io_in_progress=1,
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        # Add write latency spike (150ms)
        for i in range(5):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=20 + i),
                    device="sda",
                    reads_completed=1000,
                    reads_merged=0,
                    sectors_read=20000,
                    time_reading_ms=10000,
                    writes_completed=700 + i * 10,
                    writes_merged=0,
                    sectors_written=14000 + i * 200,
                    time_writing_ms=105000 + i * 1500,  # 150ms avg
                    io_in_progress=1,
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        detector = IOLatencyDetector(
            latency_threshold_ms=100.0, min_samples=10, confidence_threshold=0.6
        )
        anomalies = detector.detect(metrics)

        assert len(anomalies) > 0
        assert any("write" in a.type for a in anomalies)

    def test_no_anomaly_normal_latency(self):
        """Test no anomaly detected with normal latency"""
        base_time = datetime.now()
        metrics = []

        # All normal latency
        for i in range(30):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=i),
                    device="sda",
                    reads_completed=1000 + i * 10,
                    reads_merged=0,
                    sectors_read=20000 + i * 200,
                    time_reading_ms=10000 + i * 100,  # 10ms avg
                    writes_completed=500 + i * 5,
                    writes_merged=0,
                    sectors_written=10000 + i * 100,
                    time_writing_ms=2500 + i * 25,  # 5ms avg
                    io_in_progress=1,
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        detector = IOLatencyDetector(latency_threshold_ms=100.0, min_samples=10)
        anomalies = detector.detect(metrics)

        assert len(anomalies) == 0


class TestThroughputAnomalyDetector:
    """Throughput anomaly detector tests"""

    def test_throughput_detector_creation(self):
        """Test detector creation"""
        detector = ThroughputAnomalyDetector(
            drop_threshold_percent=50.0,
            spike_multiplier=3.0,
            min_samples=10,
            confidence_threshold=0.7,
        )
        assert detector.drop_threshold_percent == 50.0
        assert detector.spike_multiplier == 3.0

    def test_detect_throughput_drop(self):
        """Test detection of throughput drop"""
        base_time = datetime.now()
        metrics = []

        # Normal throughput (10MB)
        for i in range(20):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=i),
                    device="sda",
                    reads_completed=1000,
                    reads_merged=0,
                    sectors_read=20000,  # 10MB
                    time_reading_ms=10000,
                    writes_completed=500,
                    writes_merged=0,
                    sectors_written=10000,  # 5MB
                    time_writing_ms=5000,
                    io_in_progress=1,
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        # Add throughput drop (2MB)
        for i in range(5):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=20 + i),
                    device="sda",
                    reads_completed=1000,
                    reads_merged=0,
                    sectors_read=4000,  # 2MB (80% drop)
                    time_reading_ms=10000,
                    writes_completed=500,
                    writes_merged=0,
                    sectors_written=2000,  # 1MB
                    time_writing_ms=5000,
                    io_in_progress=1,
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        detector = ThroughputAnomalyDetector(
            drop_threshold_percent=50.0, min_samples=10, confidence_threshold=0.6
        )
        anomalies = detector.detect(metrics)

        assert len(anomalies) > 0
        assert any("drop" in a.type for a in anomalies)
        assert any(a.severity in ["warning", "critical"] for a in anomalies)

    def test_detect_throughput_spike(self):
        """Test detection of throughput spike"""
        base_time = datetime.now()
        metrics = []

        # Normal throughput (10MB)
        for i in range(20):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=i),
                    device="sda",
                    reads_completed=1000,
                    reads_merged=0,
                    sectors_read=20000,  # 10MB
                    time_reading_ms=10000,
                    writes_completed=500,
                    writes_merged=0,
                    sectors_written=10000,
                    time_writing_ms=5000,
                    io_in_progress=1,
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        # Add throughput spike (50MB - 5x normal)
        for i in range(5):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=20 + i),
                    device="sda",
                    reads_completed=1000,
                    reads_merged=0,
                    sectors_read=100000,  # 50MB
                    time_reading_ms=10000,
                    writes_completed=500,
                    writes_merged=0,
                    sectors_written=50000,
                    time_writing_ms=5000,
                    io_in_progress=1,
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        detector = ThroughputAnomalyDetector(
            spike_multiplier=3.0, min_samples=10, confidence_threshold=0.6
        )
        anomalies = detector.detect(metrics)

        assert len(anomalies) > 0
        assert any("spike" in a.type for a in anomalies)

    def test_no_anomaly_stable_throughput(self):
        """Test no anomaly with stable throughput"""
        base_time = datetime.now()
        metrics = []

        # Stable throughput
        for i in range(30):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=i),
                    device="sda",
                    reads_completed=1000,
                    reads_merged=0,
                    sectors_read=20000,
                    time_reading_ms=10000,
                    writes_completed=500,
                    writes_merged=0,
                    sectors_written=10000,
                    time_writing_ms=5000,
                    io_in_progress=1,
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        detector = ThroughputAnomalyDetector(min_samples=10)
        anomalies = detector.detect(metrics)

        assert len(anomalies) == 0


class TestQueueDepthDetector:
    """Queue depth anomaly detector tests"""

    def test_queue_detector_creation(self):
        """Test detector creation"""
        detector = QueueDepthDetector(
            queue_threshold=10,
            sustained_duration_ratio=0.3,
            min_samples=10,
            confidence_threshold=0.7,
        )
        assert detector.queue_threshold == 10
        assert detector.sustained_duration_ratio == 0.3

    def test_detect_high_queue_depth(self):
        """Test detection of high queue depth"""
        base_time = datetime.now()
        metrics = []

        # Normal queue depth (1-2)
        for i in range(20):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=i),
                    device="sda",
                    reads_completed=1000,
                    reads_merged=0,
                    sectors_read=20000,
                    time_reading_ms=10000,
                    writes_completed=500,
                    writes_merged=0,
                    sectors_written=10000,
                    time_writing_ms=5000,
                    io_in_progress=1 + (i % 2),  # 1-2
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        # Add high queue depth (15-25)
        for i in range(15):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=20 + i),
                    device="sda",
                    reads_completed=1000,
                    reads_merged=0,
                    sectors_read=20000,
                    time_reading_ms=10000,
                    writes_completed=500,
                    writes_merged=0,
                    sectors_written=10000,
                    time_writing_ms=5000,
                    io_in_progress=15 + i,  # High queue
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        detector = QueueDepthDetector(
            queue_threshold=10, sustained_duration_ratio=0.3, min_samples=10
        )
        anomalies = detector.detect(metrics)

        assert len(anomalies) > 0
        assert anomalies[0].type == "io_queue_congestion"
        assert anomalies[0].severity in ["warning", "critical"]

    def test_no_anomaly_normal_queue(self):
        """Test no anomaly with normal queue depth"""
        base_time = datetime.now()
        metrics = []

        # Normal queue depth
        for i in range(30):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=i),
                    device="sda",
                    reads_completed=1000,
                    reads_merged=0,
                    sectors_read=20000,
                    time_reading_ms=10000,
                    writes_completed=500,
                    writes_merged=0,
                    sectors_written=10000,
                    time_writing_ms=5000,
                    io_in_progress=1 + (i % 3),  # 1-3
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        detector = QueueDepthDetector(queue_threshold=10, min_samples=10)
        anomalies = detector.detect(metrics)

        assert len(anomalies) == 0

    def test_insufficient_samples(self):
        """Test with insufficient samples"""
        base_time = datetime.now()
        metrics = []

        # Only 5 samples
        for i in range(5):
            metrics.append(
                DiskIOMetric(
                    timestamp=base_time + timedelta(seconds=i),
                    device="sda",
                    reads_completed=1000,
                    reads_merged=0,
                    sectors_read=20000,
                    time_reading_ms=10000,
                    writes_completed=500,
                    writes_merged=0,
                    sectors_written=10000,
                    time_writing_ms=5000,
                    io_in_progress=20,  # High queue
                    time_io_ms=15000,
                    weighted_time_io_ms=16000,
                )
            )

        detector = QueueDepthDetector(min_samples=10)
        anomalies = detector.detect(metrics)

        assert len(anomalies) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
