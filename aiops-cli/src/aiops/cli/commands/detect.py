"""
Detect command group - Anomaly detection commands
"""
import time
import sys
import signal
from typing import List
import click
from aiops.config import load_config
from aiops.cpu.collectors.system_cpu import SystemCPUCollector
from aiops.cpu.detectors.static_threshold import StaticThresholdDetector
from aiops.cpu.detectors.dynamic_baseline import DynamicBaselineDetector
from aiops.cpu.models.cpu_metric import CPUMetric
from aiops.cpu.models.anomaly_event import AnomalyEvent
from aiops.cli.formatters.base import get_formatter
from aiops.core.exceptions import DetectionError, CollectionError


# Global flag for graceful shutdown
_interrupted = False


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global _interrupted
    _interrupted = True


@click.group()
def detect():
    """Detect anomalies in system metrics"""
    pass


@detect.command()
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
    help='Standard deviation multiplier for dynamic detection (default: from config or 2.0)'
)
@click.option(
    '--baseline-window',
    type=int,
    default=100,
    help='Baseline calculation window size (default: 100)'
)
@click.option(
    '--stream',
    is_flag=True,
    help='Stream mode - continuous detection until Ctrl+C'
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
def cpu(ctx, duration, algorithm, threshold, std_multiplier, baseline_window,
        stream, output, output_file, config):
    """Detect CPU anomalies

    Examples:

        \b
        # Detect with static threshold
        aiops detect cpu --duration 300 --algorithm static --threshold 90

        \b
        # Detect with dynamic baseline
        aiops detect cpu --algorithm dynamic --std-multiplier 3.0

        \b
        # Auto-select algorithm with stream mode
        aiops detect cpu --stream --algorithm auto
    """
    # Check if platform is Linux
    if ctx.obj.get('non_linux'):
        click.echo("Error: CPU detection requires Linux platform", err=True)
        click.echo("Your system: Not Linux", err=True)
        sys.exit(1)

    try:
        # Load configuration
        cfg = load_config(config)

        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)

        # Run detection
        if stream:
            _detect_stream(cfg, algorithm, threshold, std_multiplier, baseline_window,
                          output, output_file)
        else:
            _detect_batch(cfg, duration, algorithm, threshold, std_multiplier,
                         baseline_window, output, output_file)

    except (DetectionError, CollectionError) as e:
        click.echo(f"Detection error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


def _detect_batch(cfg, duration, algorithm, threshold, std_multiplier,
                  baseline_window, output_format, output_file):
    """Run batch detection (collect then detect)

    Args:
        cfg: Configuration object
        duration: Collection duration in seconds
        algorithm: Detection algorithm
        threshold: CPU threshold for static detection
        std_multiplier: Std multiplier for dynamic detection
        baseline_window: Baseline window size
        output_format: Output format
        output_file: Output file path
    """
    click.echo(f"Collecting CPU metrics for {duration} seconds...", err=True)

    # Collect metrics
    collector = SystemCPUCollector()
    collector.initialize()

    metrics = []
    start_time = time.time()
    interval = cfg.cpu.collection.interval_seconds

    try:
        while time.time() - start_time < duration:
            batch = collector.collect()
            metrics.extend(batch)
            time.sleep(interval)
    finally:
        collector.cleanup()

    click.echo(f"Collected {len(metrics)} metrics", err=True)

    # Detect anomalies
    click.echo("Running anomaly detection...", err=True)
    detector = _get_detector(cfg, algorithm, threshold, std_multiplier, baseline_window)
    anomalies = detector.detect(metrics)

    click.echo(f"Found {len(anomalies)} anomalies", err=True)

    # Format and output
    if anomalies:
        formatter = get_formatter(output_format.lower())
        formatted_output = formatter.format(anomalies)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(formatted_output)
            click.echo(f"Output saved to {output_file}")
        else:
            click.echo(formatted_output)
    else:
        click.echo("No anomalies detected")


def _detect_stream(cfg, algorithm, threshold, std_multiplier, baseline_window,
                   output_format, output_file):
    """Run stream detection (continuous collect and detect)

    Args:
        cfg: Configuration object
        algorithm: Detection algorithm
        threshold: CPU threshold for static detection
        std_multiplier: Std multiplier for dynamic detection
        baseline_window: Baseline window size
        output_format: Output format
        output_file: Output file path
    """
    global _interrupted

    click.echo("Starting continuous anomaly detection... (Press Ctrl+C to stop)", err=True)

    collector = SystemCPUCollector()
    collector.initialize()

    detector = _get_detector(cfg, algorithm, threshold, std_multiplier, baseline_window)
    interval = cfg.cpu.collection.interval_seconds

    # Buffer for detection
    metrics_buffer = []
    buffer_size = baseline_window

    formatter = get_formatter(output_format.lower())
    output_stream = open(output_file, 'w') if output_file else None

    try:
        while not _interrupted:
            # Collect metrics
            batch = collector.collect()
            metrics_buffer.extend(batch)

            # Keep buffer size manageable
            if len(metrics_buffer) > buffer_size:
                metrics_buffer = metrics_buffer[-buffer_size:]

            # Run detection if we have enough data
            if len(metrics_buffer) >= baseline_window:
                anomalies = detector.detect(metrics_buffer)

                if anomalies:
                    formatted = formatter.format(anomalies)
                    if output_stream:
                        output_stream.write(formatted + "\n")
                        output_stream.flush()
                    else:
                        click.echo(formatted)

            time.sleep(interval)

    finally:
        collector.cleanup()
        if output_stream:
            output_stream.close()
            click.echo(f"\nOutput saved to {output_file}", err=True)
        if _interrupted:
            click.echo("\nDetection stopped by user", err=True)


def _get_detector(cfg, algorithm, threshold, std_multiplier, baseline_window):
    """Get detector instance based on algorithm

    Args:
        cfg: Configuration object
        algorithm: Detection algorithm ('static', 'dynamic', 'auto')
        threshold: CPU threshold for static detection
        std_multiplier: Std multiplier for dynamic detection
        baseline_window: Baseline window size

    Returns:
        Detector instance
    """
    # Get thresholds from config or use provided values
    if threshold is None:
        threshold = cfg.cpu.detection.algorithms.static.threshold_percent

    if std_multiplier is None:
        std_multiplier = cfg.cpu.detection.algorithms.dynamic_baseline.std_multiplier

    # Auto-select algorithm
    if algorithm == 'auto':
        # Use static for simplicity (can be enhanced with heuristics)
        algorithm = 'static'
        click.echo(f"Auto-selected algorithm: {algorithm}", err=True)

    # Create detector
    if algorithm == 'static':
        return StaticThresholdDetector(
            threshold=threshold,
            duration_seconds=cfg.cpu.detection.algorithms.static.duration_seconds,
            consecutive_periods=cfg.cpu.detection.alerting.consecutive_periods
        )
    elif algorithm == 'dynamic':
        return DynamicBaselineDetector(
            window_days=cfg.cpu.detection.algorithms.dynamic_baseline.window_days,
            std_multiplier=std_multiplier,
            baseline_window=baseline_window
        )
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
