"""
Collect command group - Data collection commands
"""
import time
import sys
import signal
from datetime import datetime
from typing import List, Optional
import click
from aiops.config import load_config
from aiops.cpu.collectors.system_cpu import SystemCPUCollector
from aiops.cpu.collectors.process_cpu import ProcessCPUCollector
from aiops.cpu.models.cpu_metric import CPUMetric
from aiops.cpu.models.process_metric import ProcessMetric
from aiops.memory.collectors import SystemMemoryCollector, ProcessMemoryCollector
from aiops.memory.models import MemoryMetric, ProcessMemoryMetric
from aiops.diskio.collectors import DiskStatsCollector, ProcessIOCollector
from aiops.diskio.models import DiskIOMetric, ProcessIOMetric
from aiops.cli.formatters.base import get_formatter
from aiops.core.exceptions import CollectionError


# Global flag for graceful shutdown
_interrupted = False


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global _interrupted
    _interrupted = True


@click.group()
def collect():
    """Collect system metrics and data"""
    pass


@collect.command()
@click.option(
    '--duration',
    type=int,
    default=60,
    help='Collection duration in seconds (default: 60)'
)
@click.option(
    '--interval',
    type=float,
    default=None,
    help='Collection interval in seconds (default: from config or 1.0)'
)
@click.option(
    '--stream',
    is_flag=True,
    help='Stream mode - continuous collection until Ctrl+C'
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
    '--include-processes',
    is_flag=True,
    help='Include top process metrics'
)
@click.option(
    '--max-processes',
    type=int,
    default=10,
    help='Maximum number of processes to show (default: 10)'
)
@click.option(
    '--config',
    type=click.Path(exists=True),
    help='Path to custom config file'
)
@click.pass_context
def cpu(ctx, duration, interval, stream, output, output_file, include_processes, max_processes, config):
    """Collect CPU metrics

    Examples:

        \b
        # Collect for 30 seconds
        aiops collect cpu --duration 30

        \b
        # Stream mode with JSON output
        aiops collect cpu --stream --output json

        \b
        # Include top 20 processes
        aiops collect cpu --include-processes --max-processes 20
    """
    # Check if platform is Linux
    if ctx.obj.get('non_linux'):
        click.echo("Error: CPU collection requires Linux platform", err=True)
        click.echo("Your system: Not Linux", err=True)
        sys.exit(1)

    try:
        # Load configuration
        cfg = load_config(config)

        # Override interval if provided
        if interval is None:
            interval = cfg.cpu.collection.interval_seconds

        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)

        # Collect metrics
        if include_processes:
            metrics, processes = _collect_with_processes(
                duration, interval, stream, max_processes
            )
            data = {
                'cpu_metrics': metrics,
                'process_metrics': processes
            }
        else:
            metrics = _collect_cpu_metrics(duration, interval, stream)
            data = metrics

        # Format and output
        formatter = get_formatter(output.lower())
        formatted_output = formatter.format(data)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(formatted_output)
            click.echo(f"Output saved to {output_file}")
        else:
            click.echo(formatted_output)

    except CollectionError as e:
        click.echo(f"Collection error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


def _collect_cpu_metrics(duration: int, interval: float, stream: bool) -> List[CPUMetric]:
    """Collect CPU metrics

    Args:
        duration: Collection duration in seconds
        interval: Collection interval in seconds
        stream: Enable stream mode (continuous)

    Returns:
        List of CPUMetric objects
    """
    global _interrupted

    collector = SystemCPUCollector()
    collector.initialize()

    metrics = []
    start_time = time.time()

    try:
        click.echo("Collecting CPU metrics... (Press Ctrl+C to stop)", err=True)

        while not _interrupted:
            # Collect metrics
            batch = collector.collect()
            metrics.extend(batch)

            # Check if duration reached (only in non-stream mode)
            if not stream and (time.time() - start_time >= duration):
                break

            # Sleep for interval
            time.sleep(interval)

        return metrics

    finally:
        collector.cleanup()
        if _interrupted:
            click.echo("\nCollection stopped by user", err=True)


def _collect_with_processes(
    duration: int,
    interval: float,
    stream: bool,
    max_processes: int
) -> tuple:
    """Collect CPU metrics with process information

    Args:
        duration: Collection duration in seconds
        interval: Collection interval in seconds
        stream: Enable stream mode (continuous)
        max_processes: Maximum number of processes to collect

    Returns:
        Tuple of (cpu_metrics, process_metrics)
    """
    global _interrupted

    system_collector = SystemCPUCollector()
    process_collector = ProcessCPUCollector(max_processes=max_processes)

    system_collector.initialize()
    process_collector.initialize()

    cpu_metrics = []
    process_metrics = []
    start_time = time.time()

    try:
        click.echo("Collecting CPU and process metrics... (Press Ctrl+C to stop)", err=True)

        while not _interrupted:
            # Collect system CPU metrics
            cpu_batch = system_collector.collect()
            cpu_metrics.extend(cpu_batch)

            # Collect process metrics
            proc_batch = process_collector.collect()
            process_metrics.extend(proc_batch)

            # Check if duration reached (only in non-stream mode)
            if not stream and (time.time() - start_time >= duration):
                break

            # Sleep for interval
            time.sleep(interval)

        return cpu_metrics, process_metrics

    finally:
        system_collector.cleanup()
        process_collector.cleanup()
        if _interrupted:
            click.echo("\nCollection stopped by user", err=True)


@collect.command()
@click.option(
    '--duration',
    type=int,
    default=60,
    help='Collection duration in seconds (default: 60)'
)
@click.option(
    '--interval',
    type=float,
    default=None,
    help='Collection interval in seconds (default: from config or 1.0)'
)
@click.option(
    '--stream',
    is_flag=True,
    help='Stream mode - continuous collection until Ctrl+C'
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
    '--include-processes',
    is_flag=True,
    help='Include top process memory metrics'
)
@click.option(
    '--max-processes',
    type=int,
    default=10,
    help='Maximum number of processes to show (default: 10)'
)
@click.option(
    '--config',
    type=click.Path(exists=True),
    help='Path to custom config file'
)
@click.pass_context
def memory(ctx, duration, interval, stream, output, output_file, include_processes, max_processes, config):
    """Collect memory metrics

    Examples:

        \b
        # Collect for 30 seconds
        aiops collect memory --duration 30

        \b
        # Stream mode with JSON output
        aiops collect memory --stream --output json

        \b
        # Include top 20 processes
        aiops collect memory --include-processes --max-processes 20
    """
    # Check if platform is Linux
    if ctx.obj.get('non_linux'):
        click.echo("Error: Memory collection requires Linux platform", err=True)
        click.echo("Your system: Not Linux", err=True)
        sys.exit(1)

    try:
        # Load configuration
        cfg = load_config(config)

        # Override interval if provided
        if interval is None:
            interval = cfg.memory.collection.interval_seconds

        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)

        # Collect metrics
        if include_processes:
            metrics, processes = _collect_memory_with_processes(
                duration, interval, stream, max_processes
            )
            data = {
                'memory_metrics': metrics,
                'process_metrics': processes
            }
        else:
            metrics = _collect_memory_metrics(duration, interval, stream)
            data = metrics

        # Format and output
        formatter = get_formatter(output.lower())
        formatted_output = formatter.format(data)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(formatted_output)
            click.echo(f"Output saved to {output_file}")
        else:
            click.echo(formatted_output)

    except CollectionError as e:
        click.echo(f"Collection error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


def _collect_memory_metrics(duration: int, interval: float, stream: bool) -> List[MemoryMetric]:
    """Collect memory metrics

    Args:
        duration: Collection duration in seconds
        interval: Collection interval in seconds
        stream: Enable stream mode (continuous)

    Returns:
        List of MemoryMetric objects
    """
    global _interrupted

    collector = SystemMemoryCollector()
    collector.initialize()

    metrics = []
    start_time = time.time()

    try:
        click.echo("Collecting memory metrics... (Press Ctrl+C to stop)", err=True)

        while not _interrupted:
            # Collect metrics
            batch = collector.collect()
            metrics.extend(batch)

            # Check if duration reached (only in non-stream mode)
            if not stream and (time.time() - start_time >= duration):
                break

            # Sleep for interval
            time.sleep(interval)

        return metrics

    finally:
        collector.cleanup()
        if _interrupted:
            click.echo("\nCollection stopped by user", err=True)


def _collect_memory_with_processes(
    duration: int,
    interval: float,
    stream: bool,
    max_processes: int
) -> tuple:
    """Collect memory metrics with process information

    Args:
        duration: Collection duration in seconds
        interval: Collection interval in seconds
        stream: Enable stream mode (continuous)
        max_processes: Maximum number of processes to collect

    Returns:
        Tuple of (memory_metrics, process_metrics)
    """
    global _interrupted

    system_collector = SystemMemoryCollector()
    process_collector = ProcessMemoryCollector(max_processes=max_processes)

    system_collector.initialize()
    process_collector.initialize()

    memory_metrics = []
    process_metrics = []
    start_time = time.time()

    try:
        click.echo("Collecting memory and process metrics... (Press Ctrl+C to stop)", err=True)

        while not _interrupted:
            # Collect system memory metrics
            mem_batch = system_collector.collect()
            memory_metrics.extend(mem_batch)

            # Collect process metrics
            proc_batch = process_collector.collect()
            process_metrics.extend(proc_batch)

            # Check if duration reached (only in non-stream mode)
            if not stream and (time.time() - start_time >= duration):
                break

            # Sleep for interval
            time.sleep(interval)

        return memory_metrics, process_metrics

    finally:
        system_collector.cleanup()
        process_collector.cleanup()
        if _interrupted:
            click.echo("\nCollection stopped by user", err=True)


@collect.command()
@click.option(
    '--duration',
    type=int,
    default=60,
    help='Collection duration in seconds (default: 60)'
)
@click.option(
    '--interval',
    type=float,
    default=1.0,
    help='Collection interval in seconds (default: 1.0)'
)
@click.option(
    '--device',
    type=str,
    default=None,
    help='Specific device to monitor (e.g., sda, nvme0n1)'
)
@click.option(
    '--stream',
    is_flag=True,
    help='Stream mode - continuous collection until Ctrl+C'
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
    '--include-processes',
    is_flag=True,
    help='Include top process I/O metrics'
)
@click.option(
    '--max-processes',
    type=int,
    default=10,
    help='Maximum number of processes to show (default: 10)'
)
@click.pass_context
def diskio(ctx, duration, interval, device, stream, output, output_file, include_processes, max_processes):
    """Collect disk I/O metrics

    Examples:

        \b
        # Collect for 30 seconds
        aiops collect diskio --duration 30

        \b
        # Monitor specific device
        aiops collect diskio --device sda --stream

        \b
        # Include top 20 I/O processes
        aiops collect diskio --include-processes --max-processes 20
    """
    # Check if platform is Linux
    if ctx.obj.get('non_linux'):
        click.echo("Error: Disk I/O collection requires Linux platform", err=True)
        click.echo("Your system: Not Linux", err=True)
        sys.exit(1)

    try:
        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)

        # Collect metrics
        if include_processes:
            metrics, processes = _collect_diskio_with_processes(
                duration, interval, device, stream, max_processes
            )
            data = {
                'diskio_metrics': metrics,
                'process_metrics': processes
            }
        else:
            metrics = _collect_diskio_metrics(duration, interval, device, stream)
            data = metrics

        # Format and output
        formatter = get_formatter(output.lower())
        formatted_output = formatter.format(data)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(formatted_output)
            click.echo(f"Output saved to {output_file}")
        else:
            click.echo(formatted_output)

    except CollectionError as e:
        click.echo(f"Collection error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


def _collect_diskio_metrics(duration: int, interval: float, device: Optional[str], stream: bool) -> List[DiskIOMetric]:
    """Collect disk I/O metrics

    Args:
        duration: Collection duration in seconds
        interval: Collection interval in seconds
        device: Specific device to monitor
        stream: Enable stream mode (continuous)

    Returns:
        List of DiskIOMetric objects
    """
    global _interrupted

    collector = DiskStatsCollector(devices=[device] if device else None)
    collector.initialize()

    metrics = []
    start_time = time.time()

    try:
        click.echo("Collecting disk I/O metrics... (Press Ctrl+C to stop)", err=True)

        while not _interrupted:
            # Collect metrics
            batch = collector.collect()
            metrics.extend(batch)

            # Check if duration reached (only in non-stream mode)
            if not stream and (time.time() - start_time >= duration):
                break

            # Sleep for interval
            time.sleep(interval)

        return metrics

    finally:
        collector.cleanup()
        if _interrupted:
            click.echo("\nCollection stopped by user", err=True)


def _collect_diskio_with_processes(
    duration: int,
    interval: float,
    device: Optional[str],
    stream: bool,
    max_processes: int
) -> tuple:
    """Collect disk I/O metrics with process information

    Args:
        duration: Collection duration in seconds
        interval: Collection interval in seconds
        device: Specific device to monitor
        stream: Enable stream mode (continuous)
        max_processes: Maximum number of processes to collect

    Returns:
        Tuple of (diskio_metrics, process_metrics)
    """
    global _interrupted

    disk_collector = DiskStatsCollector(devices=[device] if device else None)
    process_collector = ProcessIOCollector(max_processes=max_processes)

    disk_collector.initialize()
    process_collector.initialize()

    diskio_metrics = []
    process_metrics = []
    start_time = time.time()

    try:
        click.echo("Collecting disk I/O and process metrics... (Press Ctrl+C to stop)", err=True)

        while not _interrupted:
            # Collect disk I/O metrics
            disk_batch = disk_collector.collect()
            diskio_metrics.extend(disk_batch)

            # Collect process metrics
            proc_batch = process_collector.collect()
            process_metrics.extend(proc_batch)

            # Check if duration reached (only in non-stream mode)
            if not stream and (time.time() - start_time >= duration):
                break

            # Sleep for interval
            time.sleep(interval)

        return diskio_metrics, process_metrics

    finally:
        disk_collector.cleanup()
        process_collector.cleanup()
        if _interrupted:
            click.echo("\nCollection stopped by user", err=True)
