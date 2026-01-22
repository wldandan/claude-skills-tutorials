"""
Logs command group - Log analysis and query commands
"""
import sys
import click
from typing import List
from aiops.config import load_config
from aiops.logs.collectors import LogCollector
from aiops.logs.models import LogEntry
from aiops.cli.formatters.base import get_formatter
from aiops.core.exceptions import CollectionError


@click.group()
def logs():
    """Log analysis and query commands"""
    pass


@logs.command()
@click.option(
    '--path',
    type=click.Path(exists=True),
    multiple=True,
    required=True,
    help='Log file path(s) to analyze'
)
@click.option(
    '--level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL'], case_sensitive=False),
    help='Filter by log level'
)
@click.option(
    '--tail',
    type=int,
    help='Number of lines to read from end of file'
)
@click.option(
    '--follow',
    is_flag=True,
    help='Follow mode (like tail -f)'
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
def query(ctx, path, level, tail, follow, output, output_file, config):
    """Query and filter log entries

    Examples:

        \b
        # Query error logs from a file
        aiops logs query --path /var/log/app.log --level ERROR

        \b
        # Get last 100 lines
        aiops logs query --path /var/log/syslog --tail 100

        \b
        # Follow logs in real-time
        aiops logs query --path /var/log/app.log --follow

        \b
        # Query multiple log files
        aiops logs query --path /var/log/app.log --path /var/log/error.log
    """
    try:
        # Load configuration
        cfg = load_config(config)

        # Create collector
        collector = LogCollector(
            log_paths=list(path),
            level_filter=level,
            tail=tail,
            follow=follow
        )
        collector.initialize()

        if follow:
            # Stream mode
            click.echo("Following logs... (Press Ctrl+C to stop)", err=True)
            try:
                for entry in collector.stream():
                    # Format and print each entry
                    formatter = get_formatter(output.lower())
                    formatted = formatter.format(entry)
                    click.echo(formatted)
            except KeyboardInterrupt:
                click.echo("\nStopped following logs", err=True)
        else:
            # Batch mode
            entries = collector.collect()

            if not entries:
                click.echo("No log entries found matching the criteria")
                return

            # Format and output
            formatter = get_formatter(output.lower())
            formatted_output = formatter.format(entries)

            if output_file:
                with open(output_file, 'w') as f:
                    f.write(formatted_output)
                click.echo(f"Output saved to {output_file}")
            else:
                click.echo(formatted_output)

        collector.cleanup()

    except CollectionError as e:
        click.echo(f"Collection error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


@logs.command()
@click.option(
    '--path',
    type=click.Path(exists=True),
    multiple=True,
    required=True,
    help='Log file path(s) to analyze'
)
@click.option(
    '--output',
    type=click.Choice(['table', 'json', 'yaml'], case_sensitive=False),
    default='table',
    help='Output format (default: table)'
)
@click.option(
    '--config',
    type=click.Path(exists=True),
    help='Path to custom config file'
)
@click.pass_context
def stats(ctx, path, output, config):
    """Generate log statistics

    Examples:

        \b
        # Generate statistics for a log file
        aiops logs stats --path /var/log/app.log

        \b
        # Statistics for multiple files
        aiops logs stats --path /var/log/app.log --path /var/log/error.log
    """
    try:
        # Load configuration
        cfg = load_config(config)

        # Create collector
        collector = LogCollector(log_paths=list(path))
        collector.initialize()

        # Collect all entries
        entries = collector.collect()

        if not entries:
            click.echo("No log entries found")
            return

        # Calculate statistics
        stats_data = _calculate_statistics(entries)

        # Format and output
        formatter = get_formatter(output.lower())
        formatted_output = formatter.format(stats_data)
        click.echo(formatted_output)

        collector.cleanup()

    except CollectionError as e:
        click.echo(f"Collection error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


def _calculate_statistics(entries: List[LogEntry]) -> dict:
    """Calculate statistics from log entries.

    Args:
        entries: List of LogEntry objects

    Returns:
        Dictionary with statistics
    """
    from collections import Counter

    total = len(entries)
    level_counts = Counter(entry.level for entry in entries)
    source_counts = Counter(entry.source for entry in entries)
    process_counts = Counter(entry.process for entry in entries if entry.process)

    # Calculate error rate
    error_count = sum(count for level, count in level_counts.items()
                     if level in ['ERROR', 'CRITICAL', 'FATAL'])
    error_rate = (error_count / total * 100) if total > 0 else 0

    return {
        'total_entries': total,
        'level_distribution': dict(level_counts),
        'error_rate': error_rate,
        'top_sources': dict(source_counts.most_common(10)),
        'top_processes': dict(process_counts.most_common(10)),
        'time_range': {
            'start': min(entry.timestamp for entry in entries).isoformat(),
            'end': max(entry.timestamp for entry in entries).isoformat(),
        }
    }
