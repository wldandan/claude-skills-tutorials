"""
Monitor command group - Real-time monitoring commands
"""
import time
import sys
import signal
from datetime import datetime
from typing import List, Optional
import click
from aiops.config import load_config
from aiops.process.collectors import ProcessStatusCollector
from aiops.process.models import ProcessStatusMetric
from aiops.cli.formatters.base import get_formatter
from aiops.core.exceptions import CollectionError


# Global flag for graceful shutdown
_interrupted = False


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global _interrupted
    _interrupted = True


@click.group()
def monitor():
    """Real-time monitoring of system resources"""
    pass


@monitor.command()
@click.option(
    '--interval',
    type=int,
    default=10,
    help='Monitoring interval in seconds (default: 10)'
)
@click.option(
    '--pids',
    type=str,
    help='Comma-separated list of PIDs to monitor (e.g., "1234,5678")'
)
@click.option(
    '--include-zombies',
    is_flag=True,
    help='Include zombie processes in monitoring'
)
@click.option(
    '--max-processes',
    type=int,
    default=20,
    help='Maximum number of processes to show (default: 20)'
)
@click.option(
    '--sort-by',
    type=click.Choice(['cpu', 'memory', 'pid', 'name'], case_sensitive=False),
    default='cpu',
    help='Sort processes by field (default: cpu)'
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
def processes(ctx, interval, pids, include_zombies, max_processes, sort_by, output, output_file, config):
    """Monitor process health and status

    Examples:

        \b
        # Monitor all processes
        aiops monitor processes

        \b
        # Monitor specific processes
        aiops monitor processes --pids "1234,5678"

        \b
        # Include zombie processes
        aiops monitor processes --include-zombies

        \b
        # Sort by memory usage
        aiops monitor processes --sort-by memory --max-processes 30
    """
    # Check if platform is Linux
    if ctx.obj.get('non_linux'):
        click.echo("Error: Process monitoring requires Linux platform", err=True)
        click.echo("Your system: Not Linux", err=True)
        sys.exit(1)

    try:
        # Load configuration
        cfg = load_config(config)

        # Parse PIDs if provided
        pid_list = None
        if pids:
            try:
                pid_list = [int(p.strip()) for p in pids.split(',')]
            except ValueError:
                click.echo("Error: Invalid PID format. Use comma-separated integers.", err=True)
                sys.exit(1)

        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)

        # Monitor processes
        metrics = _monitor_processes(
            interval=interval,
            pids=pid_list,
            include_zombies=include_zombies,
            max_processes=max_processes,
            sort_by=sort_by
        )

        # Format and output
        formatter = get_formatter(output.lower())
        formatted_output = formatter.format(metrics)

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


def _monitor_processes(
    interval: int,
    pids: Optional[List[int]],
    include_zombies: bool,
    max_processes: int,
    sort_by: str
) -> List[ProcessStatusMetric]:
    """Monitor process health and status

    Args:
        interval: Monitoring interval in seconds
        pids: List of specific PIDs to monitor
        include_zombies: Include zombie processes
        max_processes: Maximum number of processes to show
        sort_by: Field to sort by

    Returns:
        List of ProcessStatusMetric objects
    """
    global _interrupted

    collector = ProcessStatusCollector(pids=pids, include_all=include_zombies)
    collector.initialize()

    all_metrics = []

    try:
        click.echo("Monitoring processes... (Press Ctrl+C to stop)", err=True)

        while not _interrupted:
            # Collect process metrics
            metrics = collector.collect()

            # Sort metrics
            if sort_by == 'cpu':
                metrics.sort(key=lambda m: m.cpu_percent, reverse=True)
            elif sort_by == 'memory':
                metrics.sort(key=lambda m: m.memory_percent, reverse=True)
            elif sort_by == 'pid':
                metrics.sort(key=lambda m: m.pid)
            elif sort_by == 'name':
                metrics.sort(key=lambda m: m.name)

            # Limit to max_processes
            metrics = metrics[:max_processes]

            # Display current snapshot
            if output == 'table':
                # Clear screen and show current state
                click.clear()
                click.echo(f"Process Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                click.echo(f"Total processes: {len(metrics)}")
                if pids:
                    click.echo(f"Monitoring PIDs: {', '.join(map(str, pids))}")
                click.echo("")

                # Format and display
                from aiops.cli.formatters.table import TableFormatter
                formatter = TableFormatter()
                click.echo(formatter._format_process_status_metrics(metrics))

            all_metrics.extend(metrics)

            # Sleep for interval
            time.sleep(interval)

        return all_metrics

    finally:
        collector.cleanup()
        if _interrupted:
            click.echo("\nMonitoring stopped by user", err=True)
