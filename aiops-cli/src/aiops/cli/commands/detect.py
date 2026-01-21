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
from aiops.memory.collectors import SystemMemoryCollector, ProcessMemoryCollector
from aiops.memory.detectors import MemoryLeakDetector, OOMRiskDetector, SwapAnomalyDetector
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


@detect.command()
@click.option(
    '--duration',
    type=int,
    default=300,
    help='Analysis duration in seconds (default: 300)'
)
@click.option(
    '--algorithm',
    type=click.Choice(['leak', 'oom', 'swap', 'auto'], case_sensitive=False),
    default='auto',
    help='Detection algorithm (default: auto)'
)
@click.option(
    '--pid',
    type=int,
    default=None,
    help='Specific process ID to analyze for memory leaks'
)
@click.option(
    '--growth-threshold',
    type=float,
    default=None,
    help='Memory growth threshold MB/hour for leak detection (default: from config or 50.0)'
)
@click.option(
    '--risk-threshold',
    type=float,
    default=None,
    help='Memory usage threshold percent for OOM risk (default: from config or 90.0)'
)
@click.option(
    '--swap-threshold',
    type=float,
    default=None,
    help='Swap usage threshold percent (default: from config or 10.0)'
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
def memory(ctx, duration, algorithm, pid, growth_threshold, risk_threshold,
           swap_threshold, stream, output, output_file, config):
    """Detect memory anomalies

    Examples:

        \b
        # Detect memory leaks
        aiops detect memory --duration 300 --algorithm leak

        \b
        # Detect OOM risk
        aiops detect memory --algorithm oom --risk-threshold 85

        \b
        # Detect swap anomalies
        aiops detect memory --algorithm swap

        \b
        # Auto-detect all memory issues
        aiops detect memory --duration 600 --algorithm auto
    """
    # Check if platform is Linux
    if ctx.obj.get('non_linux'):
        click.echo("Error: Memory detection requires Linux platform", err=True)
        click.echo("Your system: Not Linux", err=True)
        sys.exit(1)

    try:
        # Load configuration
        cfg = load_config(config)

        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)

        if stream:
            _detect_memory_stream(
                cfg, algorithm, pid, growth_threshold, risk_threshold,
                swap_threshold, output, output_file
            )
        else:
            _detect_memory_batch(
                cfg, duration, algorithm, pid, growth_threshold, risk_threshold,
                swap_threshold, output, output_file
            )

    except (DetectionError, CollectionError) as e:
        click.echo(f"Detection error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _detect_memory_batch(cfg, duration, algorithm, pid, growth_threshold,
                         risk_threshold, swap_threshold, output_format, output_file):
    """Run batch detection (collect then detect)

    Args:
        cfg: Configuration object
        duration: Collection duration in seconds
        algorithm: Detection algorithm
        pid: Specific process ID (for leak detection)
        growth_threshold: Memory growth threshold
        risk_threshold: OOM risk threshold
        swap_threshold: Swap usage threshold
        output_format: Output format
        output_file: Output file path
    """
    click.echo(f"Collecting memory metrics for {duration} seconds...", err=True)

    # Collect metrics based on algorithm
    if algorithm in ['leak', 'auto'] and pid:
        # Collect specific process metrics
        collector = ProcessMemoryCollector()
        collector.initialize()
        metrics = []
        start_time = time.time()
        interval = cfg.memory.collection.interval_seconds

        try:
            while time.time() - start_time < duration:
                batch = collector.collect(pid=pid)
                metrics.extend(batch)
                time.sleep(interval)
        finally:
            collector.cleanup()
    else:
        # Collect system memory metrics
        system_collector = SystemMemoryCollector()
        system_collector.initialize()
        system_metrics = []

        # Also collect process metrics for leak detection
        process_collector = ProcessMemoryCollector(max_processes=20)
        process_collector.initialize()
        process_metrics = []

        start_time = time.time()
        interval = cfg.memory.collection.interval_seconds

        try:
            while time.time() - start_time < duration:
                sys_batch = system_collector.collect()
                system_metrics.extend(sys_batch)

                if algorithm in ['leak', 'auto']:
                    proc_batch = process_collector.collect()
                    process_metrics.extend(proc_batch)

                time.sleep(interval)
        finally:
            system_collector.cleanup()
            process_collector.cleanup()

        metrics = (system_metrics, process_metrics)

    click.echo(f"Collected metrics", err=True)

    # Detect anomalies
    click.echo("Running anomaly detection...", err=True)
    anomalies = _run_memory_detection(
        cfg, algorithm, metrics, growth_threshold, risk_threshold, swap_threshold
    )

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


def _detect_memory_stream(cfg, algorithm, pid, growth_threshold, risk_threshold,
                          swap_threshold, output_format, output_file):
    """Run stream detection (continuous collect and detect)

    Args:
        cfg: Configuration object
        algorithm: Detection algorithm
        pid: Specific process ID
        growth_threshold: Memory growth threshold
        risk_threshold: OOM risk threshold
        swap_threshold: Swap usage threshold
        output_format: Output format
        output_file: Output file path
    """
    global _interrupted

    click.echo("Starting stream detection... (Press Ctrl+C to stop)", err=True)

    # Initialize collectors
    system_collector = SystemMemoryCollector()
    system_collector.initialize()
    system_metrics = []

    process_collector = ProcessMemoryCollector(max_processes=20)
    process_collector.initialize()
    process_metrics = []

    interval = cfg.memory.collection.interval_seconds
    detection_window = 100  # Detect every 100 samples

    # Open output file if specified
    output_stream = None
    if output_file:
        output_stream = open(output_file, 'w')

    try:
        while not _interrupted:
            # Collect metrics
            sys_batch = system_collector.collect()
            system_metrics.extend(sys_batch)

            if algorithm in ['leak', 'auto']:
                proc_batch = process_collector.collect()
                process_metrics.extend(proc_batch)

            # Run detection periodically
            if len(system_metrics) >= detection_window:
                anomalies = _run_memory_detection(
                    cfg, algorithm, (system_metrics, process_metrics),
                    growth_threshold, risk_threshold, swap_threshold
                )

                if anomalies:
                    formatter = get_formatter(output_format.lower())
                    formatted_output = formatter.format(anomalies)

                    if output_stream:
                        output_stream.write(formatted_output + "\n")
                        output_stream.flush()
                    else:
                        click.echo(formatted_output)

                # Keep only recent metrics
                system_metrics = system_metrics[-detection_window:]
                process_metrics = process_metrics[-detection_window:]

            time.sleep(interval)

    finally:
        system_collector.cleanup()
        process_collector.cleanup()
        if output_stream:
            output_stream.close()
            click.echo(f"\nOutput saved to {output_file}", err=True)
        if _interrupted:
            click.echo("\nDetection stopped by user", err=True)


def _run_memory_detection(cfg, algorithm, metrics, growth_threshold,
                          risk_threshold, swap_threshold):
    """Run memory anomaly detection

    Args:
        cfg: Configuration object
        algorithm: Detection algorithm
        metrics: Collected metrics (system_metrics, process_metrics) tuple or process list
        growth_threshold: Memory growth threshold
        risk_threshold: OOM risk threshold
        swap_threshold: Swap usage threshold

    Returns:
        List of detected anomalies
    """
    all_anomalies = []

    # Unpack metrics
    if isinstance(metrics, tuple):
        system_metrics, process_metrics = metrics
    else:
        # Single process metrics
        system_metrics = []
        process_metrics = metrics

    # Get thresholds from config or use provided values
    if growth_threshold is None:
        growth_threshold = cfg.memory.detection.algorithms.memory_leak.growth_threshold_mb

    if risk_threshold is None:
        risk_threshold = cfg.memory.detection.algorithms.oom_risk.risk_threshold_percent

    if swap_threshold is None:
        swap_threshold = cfg.memory.detection.algorithms.swap_anomaly.threshold_percent

    # Run detection based on algorithm
    if algorithm == 'leak' or algorithm == 'auto':
        if process_metrics:
            leak_detector = MemoryLeakDetector(
                min_samples=cfg.memory.detection.algorithms.memory_leak.min_samples,
                growth_threshold_mb=growth_threshold,
                confidence_threshold=cfg.memory.detection.algorithms.memory_leak.confidence_threshold
            )
            leak_anomalies = leak_detector.detect(process_metrics)
            all_anomalies.extend(leak_anomalies)

    if algorithm == 'oom' or algorithm == 'auto':
        if system_metrics:
            oom_detector = OOMRiskDetector(
                prediction_window_hours=cfg.memory.detection.algorithms.oom_risk.prediction_window_hours,
                risk_threshold_percent=risk_threshold
            )
            oom_anomalies = oom_detector.detect(system_metrics)
            all_anomalies.extend(oom_anomalies)

    if algorithm == 'swap' or algorithm == 'auto':
        if system_metrics:
            swap_detector = SwapAnomalyDetector(
                threshold_percent=swap_threshold,
                spike_multiplier=cfg.memory.detection.algorithms.swap_anomaly.spike_multiplier
            )
            swap_anomalies = swap_detector.detect(system_metrics)
            all_anomalies.extend(swap_anomalies)

    return all_anomalies
