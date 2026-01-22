"""Root cause analysis module."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter


class RootCauseAnalyzer:
    """Analyze and identify root causes of anomalies."""

    def __init__(self):
        """Initialize root cause analyzer."""
        pass

    def analyze(
        self,
        anomaly_events: List[Any],
        metrics_data: Optional[Dict[str, List[float]]] = None,
        log_entries: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """Analyze root cause of anomalies.

        Args:
            anomaly_events: List of anomaly events
            metrics_data: Optional metrics data
            log_entries: Optional log entries

        Returns:
            Root cause analysis result
        """
        if not anomaly_events:
            return {
                'root_cause': None,
                'confidence': 0.0,
                'evidence': [],
                'recommendations': [],
            }

        # Analyze anomaly types
        anomaly_types = [e.type for e in anomaly_events]
        type_counts = Counter(anomaly_types)

        # Find most common anomaly type
        most_common_type = type_counts.most_common(1)[0][0]
        most_common_count = type_counts.most_common(1)[0][1]

        # Calculate confidence based on consistency
        confidence = most_common_count / len(anomaly_events)

        # Determine root cause based on anomaly patterns
        root_cause = self._determine_root_cause(anomaly_events, type_counts)

        # Collect evidence
        evidence = self._collect_evidence(anomaly_events, metrics_data, log_entries)

        # Generate recommendations
        recommendations = self._generate_recommendations(root_cause, anomaly_events)

        return {
            'root_cause': root_cause,
            'confidence': confidence,
            'primary_anomaly_type': most_common_type,
            'anomaly_count': len(anomaly_events),
            'anomaly_distribution': dict(type_counts),
            'evidence': evidence,
            'recommendations': recommendations,
            'analysis_time': datetime.now().isoformat(),
        }

    def _determine_root_cause(
        self,
        anomaly_events: List[Any],
        type_counts: Counter
    ) -> str:
        """Determine root cause from anomaly patterns.

        Args:
            anomaly_events: List of anomaly events
            type_counts: Counter of anomaly types

        Returns:
            Root cause description
        """
        # Check for specific patterns
        types = set(type_counts.keys())

        # CPU-related patterns
        if 'high_cpu' in types or 'cpu_spike' in types:
            if 'memory_leak' in types:
                return "CPU exhaustion due to memory leak causing excessive GC"
            elif 'process_crash' in types:
                return "CPU spike followed by process crash"
            else:
                return "CPU resource exhaustion"

        # Memory-related patterns
        if 'memory_leak' in types or 'oom_risk' in types:
            return "Memory leak leading to OOM risk"

        # Disk I/O patterns
        if 'io_latency_spike' in types or 'io_bottleneck' in types:
            if 'high_cpu' in types:
                return "I/O bottleneck causing CPU wait"
            else:
                return "Disk I/O performance degradation"

        # Network patterns
        if 'network_anomaly' in types or 'connection_spike' in types:
            return "Network connectivity or bandwidth issue"

        # Process patterns
        if 'zombie_process' in types:
            return "Zombie processes indicating parent process issues"
        if 'process_crash' in types:
            return "Process instability or crash"

        # Log patterns
        if 'high_error_rate' in types or 'log_storm' in types:
            return "Application errors or logging issues"

        # Default
        most_common = type_counts.most_common(1)[0][0]
        return f"Anomaly pattern: {most_common}"

    def _collect_evidence(
        self,
        anomaly_events: List[Any],
        metrics_data: Optional[Dict[str, List[float]]],
        log_entries: Optional[List[Any]]
    ) -> List[Dict[str, Any]]:
        """Collect evidence supporting root cause.

        Args:
            anomaly_events: List of anomaly events
            metrics_data: Optional metrics data
            log_entries: Optional log entries

        Returns:
            List of evidence items
        """
        evidence = []

        # Evidence from anomaly events
        for event in anomaly_events[:5]:  # Top 5 events
            evidence.append({
                'type': 'anomaly_event',
                'timestamp': event.timestamp.isoformat(),
                'anomaly_type': event.type,
                'severity': event.severity,
                'confidence': event.confidence,
                'metrics': event.metrics,
            })

        # Evidence from metrics
        if metrics_data:
            for metric_name, values in metrics_data.items():
                if len(values) > 0:
                    evidence.append({
                        'type': 'metric',
                        'metric_name': metric_name,
                        'max_value': max(values),
                        'min_value': min(values),
                        'avg_value': sum(values) / len(values),
                    })

        # Evidence from logs
        if log_entries:
            error_logs = [log for log in log_entries if log.is_error]
            if error_logs:
                evidence.append({
                    'type': 'logs',
                    'error_count': len(error_logs),
                    'sample_errors': [log.message for log in error_logs[:3]],
                })

        return evidence

    def _generate_recommendations(
        self,
        root_cause: str,
        anomaly_events: List[Any]
    ) -> List[str]:
        """Generate recommendations based on root cause.

        Args:
            root_cause: Identified root cause
            anomaly_events: List of anomaly events

        Returns:
            List of recommendations
        """
        recommendations = []

        # CPU-related recommendations
        if 'CPU' in root_cause or 'cpu' in root_cause.lower():
            recommendations.append("Check top CPU-consuming processes")
            recommendations.append("Review application performance and optimize hot paths")
            recommendations.append("Consider scaling up CPU resources")

        # Memory-related recommendations
        if 'memory' in root_cause.lower() or 'leak' in root_cause.lower():
            recommendations.append("Investigate memory leaks in application")
            recommendations.append("Review heap dumps and memory profiles")
            recommendations.append("Increase memory limits or optimize memory usage")

        # I/O-related recommendations
        if 'I/O' in root_cause or 'io' in root_cause.lower() or 'disk' in root_cause.lower():
            recommendations.append("Check disk I/O performance and queue depth")
            recommendations.append("Optimize database queries and file operations")
            recommendations.append("Consider using faster storage (SSD/NVMe)")

        # Network-related recommendations
        if 'network' in root_cause.lower() or 'connection' in root_cause.lower():
            recommendations.append("Check network connectivity and bandwidth")
            recommendations.append("Review firewall rules and network configuration")
            recommendations.append("Optimize connection pooling and timeouts")

        # Process-related recommendations
        if 'process' in root_cause.lower() or 'crash' in root_cause.lower():
            recommendations.append("Review application logs for crash reasons")
            recommendations.append("Check for segmentation faults or OOM kills")
            recommendations.append("Implement proper error handling and recovery")

        # Log-related recommendations
        if 'log' in root_cause.lower() or 'error' in root_cause.lower():
            recommendations.append("Review application error logs")
            recommendations.append("Fix identified errors and exceptions")
            recommendations.append("Implement proper logging levels and rotation")

        # Default recommendations
        if not recommendations:
            recommendations.append("Review system metrics during anomaly period")
            recommendations.append("Check application logs for errors")
            recommendations.append("Monitor system for recurring patterns")

        return recommendations

    def generate_timeline(
        self,
        anomaly_events: List[Any],
        window_minutes: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate event timeline.

        Args:
            anomaly_events: List of anomaly events
            window_minutes: Time window in minutes

        Returns:
            Timeline of events
        """
        # Sort events by timestamp
        sorted_events = sorted(anomaly_events, key=lambda e: e.timestamp)

        timeline = []
        for event in sorted_events:
            timeline.append({
                'timestamp': event.timestamp.isoformat(),
                'type': event.type,
                'severity': event.severity,
                'confidence': event.confidence,
                'description': f"{event.type} detected with {event.severity} severity",
            })

        return timeline
