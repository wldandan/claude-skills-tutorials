"""
Analyze command group - Combined analysis commands
"""
import time
import sys
from datetime import datetime
from typing import Dict, List
import click
from aiops.config import load_config
from aiops.cpu.collectors.system_cpu import SystemCPUCollector
from aiops.cpu.collectors.process_cpu import ProcessCPUCollector
from aiops.cpu.detectors.static_threshold import StaticThresholdDetector
from aiops.cpu.detectors.dynamic_baseline import DynamicBaselineDetector
from aiops.cpu.models.cpu_metric import CPUMetric
from aiops.cpu.models.anomaly_event import AnomalyEvent
from aiops.cpu.models.process_metric import ProcessMetric
from aiops.cli.formatters.base import get_formatter
from aiops.core.exceptions import AnalysisError, CollectionError, DetectionError


@click.group()
def analyze():
    """Perform comprehensive system analysis"""
    pass


@analyze.command()
@click.option(
    '--duration',
    type=int,
    default=300,
    help='Analysis duration in seconds (default: 300)'
)
@click.option(
    '--algorithm',
    type=click.Choice(['static', 'dynamic', 'auto'], case_sensitive=False),
    default='auto',
    help='Detection algorithm (default: auto)'
)
@click.option(
    '--threshold',
    type=float,
    default=None,
    help='CPU threshold for static detection (default: from config or 80.0)'
)
@click.option(
    '--std-multiplier',
    type=float,
    default=None,
    help='Standard deviation multiplier for dynamic detection (default: 2.0)'
)
@click.option(
    '--include-baseline',
    is_flag=True,
    help='Include baseline statistics in report'
)
@click.option(
    '--include-processes',
    is_flag=True,
    help='Include top process metrics in report'
)
@click.option(
    '--max-processes',
    type=int,
    default=10,
    help='Maximum number of processes to include (default: 10)'
)
@click.option(
    '--output',
    type=click.Choice(['table', 'json', 'yaml'], case_sensitive=False),
    default='table',
    help='Output format (default: table)'
)
@click.option(
    '--output-file',
    type=click.Path(),
    help='Save output to file instead of stdout'
)
@click.option(
    '--config',
    type=click.Path(exists=True),
    help='Path to custom config file'
)
@click.pass_context
def cpu(ctx, duration, algorithm, threshold, std_multiplier, include_baseline,
        include_processes, max_processes, output, output_file, config):
    """Analyze CPU metrics with comprehensive reporting

    This command combines data collection, anomaly detection, and generates
    a detailed analysis report including summary statistics, anomalies,
    baseline information, and top processes.

    Examples:

        \b
        # Full analysis with all features
        aiops analyze cpu --duration 600 --include-baseline --include-processes

        \b
        # Quick analysis with specific algorithm
        aiops analyze cpu --duration 120 --algorithm dynamic
    """
    # Check if platform is Linux
    if ctx.obj.get('non_linux'):
        click.echo("Error: CPU analysis requires Linux platform", err=True)
        click.echo("Your system: Not Linux", err=True)
        sys.exit(1)

    try:
        # Load configuration
        cfg = load_config(config)

        # Run analysis
        report = _perform_analysis(
            cfg,
            duration,
            algorithm,
            threshold,
            std_multiplier,
            include_baseline,
            include_processes,
            max_processes
        )

        # Format and output
        formatter = get_formatter(output.lower())
        formatted_output = formatter.format(report)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(formatted_output)
            click.echo(f"Analysis report saved to {output_file}")
        else:
            click.echo(formatted_output)

    except (AnalysisError, CollectionError, DetectionError) as e:
        click.echo(f"Analysis error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


def _perform_analysis(cfg, duration, algorithm, threshold, std_multiplier,
                     include_baseline, include_processes, max_processes) -> Dict:
    """Perform comprehensive CPU analysis

    Args:
        cfg: Configuration object
        duration: Analysis duration in seconds
        algorithm: Detection algorithm
        threshold: CPU threshold for static detection
        std_multiplier: Std multiplier for dynamic detection
        include_baseline: Include baseline statistics
        include_processes: Include process metrics
        max_processes: Maximum number of processes

    Returns:
        Analysis report dict
    """
    click.echo(f"Starting CPU analysis for {duration} seconds...", err=True)

    # Phase 1: Data Collection
    click.echo("Phase 1/3: Collecting metrics...", err=True)
    start_time = time.time()

    system_collector = SystemCPUCollector()
    system_collector.initialize()

    cpu_metrics = []
    process_metrics = []
    interval = cfg.cpu.collection.interval_seconds

    if include_processes:
        process_collector = ProcessCPUCollector(max_processes=max_processes)
        process_collector.initialize()

    try:
        collection_start = time.time()
        while time.time() - collection_start < duration:
            # Collect CPU metrics
            batch = system_collector.collect()
            cpu_metrics.extend(batch)

            # Collect process metrics if requested
            if include_processes:
                proc_batch = process_collector.collect()
                process_metrics.extend(proc_batch)

            time.sleep(interval)

    finally:
        system_collector.cleanup()
        if include_processes:
            process_collector.cleanup()

    end_time = time.time()
    click.echo(f"Collected {len(cpu_metrics)} CPU metrics", err=True)

    # Phase 2: Anomaly Detection
    click.echo("Phase 2/3: Detecting anomalies...", err=True)

    # Get detector
    if threshold is None:
        threshold = cfg.cpu.detection.algorithms.static.threshold_percent
    if std_multiplier is None:
        std_multiplier = cfg.cpu.detection.algorithms.dynamic_baseline.std_multiplier

    if algorithm == 'auto':
        algorithm = 'static'
        click.echo(f"Auto-selected algorithm: {algorithm}", err=True)

    if algorithm == 'static':
        detector = StaticThresholdDetector(
            threshold=threshold,
            duration_seconds=cfg.cpu.detection.algorithms.static.duration_seconds,
            consecutive_periods=cfg.cpu.detection.alerting.consecutive_periods
        )
    else:  # dynamic
        detector = DynamicBaselineDetector(
            window_days=cfg.cpu.detection.algorithms.dynamic_baseline.window_days,
            std_multiplier=std_multiplier,
            baseline_window=100
        )

    anomalies = detector.detect(cpu_metrics)
    click.echo(f"Detected {len(anomalies)} anomalies", err=True)

    # Phase 3: Generate Report
    click.echo("Phase 3/3: Generating report...", err=True)

    report = _generate_report(
        cpu_metrics,
        anomalies,
        process_metrics,
        algorithm,
        threshold,
        std_multiplier,
        include_baseline,
        start_time,
        end_time
    )

    return report


def _generate_report(cpu_metrics, anomalies, process_metrics, algorithm,
                    threshold, std_multiplier, include_baseline,
                    start_time, end_time) -> Dict:
    """Generate analysis report

    Args:
        cpu_metrics: List of CPU metrics
        anomalies: List of anomaly events
        process_metrics: List of process metrics
        algorithm: Detection algorithm used
        threshold: Threshold value
        std_multiplier: Std multiplier value
        include_baseline: Include baseline stats
        start_time: Analysis start time
        end_time: Analysis end time

    Returns:
        Report dict
    """
    # Calculate summary statistics
    cpu_values = [m.cpu_percent for m in cpu_metrics]
    summary = {
        'analysis_period': {
            'start': datetime.fromtimestamp(start_time).isoformat(),
            'end': datetime.fromtimestamp(end_time).isoformat(),
            'duration_seconds': int(end_time - start_time)
        },
        'metrics_collected': len(cpu_metrics),
        'anomalies_detected': len(anomalies),
        'algorithm_used': algorithm,
        'cpu_statistics': {
            'min': min(cpu_values) if cpu_values else 0.0,
            'max': max(cpu_values) if cpu_values else 0.0,
            'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0.0,
        }
    }

    # Anomaly breakdown by severity
    severity_counts = {}
    for anomaly in anomalies:
        severity = anomaly.severity
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    summary['anomaly_breakdown'] = severity_counts

    # Build report
    report = {
        'summary': summary,
        'anomalies': [a.to_dict() for a in anomalies] if anomalies else []
    }

    # Add baseline statistics if requested
    if include_baseline:
        import numpy as np
        cpu_array = np.array(cpu_values)
        report['baseline'] = {
            'mean': float(np.mean(cpu_array)),
            'std': float(np.std(cpu_array)),
            'median': float(np.median(cpu_array)),
            'percentile_95': float(np.percentile(cpu_array, 95)),
            'percentile_99': float(np.percentile(cpu_array, 99)),
            'threshold_used': threshold,
            'std_multiplier_used': std_multiplier
        }

    # Add process metrics if requested
    if process_metrics:
        # Get unique top processes (latest snapshot)
        latest_processes = process_metrics[-10:] if len(process_metrics) > 10 else process_metrics
        report['top_processes'] = [p.to_dict() for p in latest_processes]

    return report
