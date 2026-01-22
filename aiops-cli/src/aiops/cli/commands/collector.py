"""
Collector command - Unified data collection
"""
import sys
import time
import json
import click
from datetime import datetime
from aiops.config import load_config
from aiops.cpu.collectors import SystemCPUCollector
from aiops.memory.collectors import SystemMemoryCollector
from aiops.diskio.collectors import DiskStatsCollector
from aiops.network.collectors import NetworkStatsCollector
from aiops.process.collectors import ProcessStatusCollector
from aiops.core.exceptions import CollectionError


@click.group()
def collector():
    """Unified data collector service"""
    pass


@collector.command()
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
    '--output',
    type=click.Path(),
    help='Output file path (JSON format)'
)
@click.option(
    '--metrics',
    type=str,
    default='cpu,memory,disk,network',
    help='Metrics to collect (comma-separated: cpu,memory,disk,network,process)'
)
@click.option(
    '--config',
    type=click.Path(exists=True),
    help='Path to custom config file'
)
@click.pass_context
def run(ctx, duration, interval, output, metrics, config):
    """Run unified data collection

    Examples:

        \b
        # Collect all metrics for 60 seconds
        aiops collector run --duration 60

        \b
        # Collect only CPU and memory
        aiops collector run --metrics cpu,memory --duration 30

        \b
        # Save to file
        aiops collector run --output metrics.json --duration 60
    """
    try:
        # Load configuration
        cfg = load_config(config)

        # Parse metrics
        metric_types = [m.strip() for m in metrics.split(',')]

        # Initialize collectors
        collectors_map = {}

        if 'cpu' in metric_types:
            cpu_collector = SystemCPUCollector()
            cpu_collector.initialize()
            collectors_map['cpu'] = cpu_collector

        if 'memory' in metric_types:
            mem_collector = SystemMemoryCollector()
            mem_collector.initialize()
            collectors_map['memory'] = mem_collector

        if 'disk' in metric_types:
            disk_collector = DiskStatsCollector()
            disk_collector.initialize()
            collectors_map['disk'] = disk_collector

        if 'network' in metric_types:
            net_collector = NetworkStatsCollector()
            net_collector.initialize()
            collectors_map['network'] = net_collector

        if 'process' in metric_types:
            proc_collector = ProcessStatusCollector()
            proc_collector.initialize()
            collectors_map['process'] = proc_collector

        # Collect data
        click.echo(f"Starting collection for {duration}s (interval={interval}s)...", err=True)

        all_data = []
        start_time = time.time()

        while time.time() - start_time < duration:
            snapshot = {
                'timestamp': datetime.now().isoformat(),
            }

            # Collect from each collector
            for metric_type, collector in collectors_map.items():
                try:
                    data = collector.collect()
                    snapshot[metric_type] = [m.to_dict() if hasattr(m, 'to_dict') else str(m) for m in data]
                except Exception as e:
                    click.echo(f"Error collecting {metric_type}: {e}", err=True)

            all_data.append(snapshot)

            # Wait for next interval
            time.sleep(interval)

        # Cleanup collectors
        for collector in collectors_map.values():
            collector.cleanup()

        # Output results
        output_data = {
            'collection_info': {
                'start_time': datetime.fromtimestamp(start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': duration,
                'interval_seconds': interval,
                'metrics_collected': list(collectors_map.keys()),
                'total_snapshots': len(all_data),
            },
            'data': all_data,
        }

        if output:
            with open(output, 'w') as f:
                json.dump(output_data, f, indent=2)
            click.echo(f"Data saved to {output}")
        else:
            click.echo(json.dumps(output_data, indent=2))

    except CollectionError as e:
        click.echo(f"Collection error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


@collector.command()
@click.pass_context
def status(ctx):
    """Show collector status

    Examples:

        \b
        # Check collector status
        aiops collector status
    """
    click.echo("Collector Status:")
    click.echo("  Mode: On-demand (no daemon)")
    click.echo("  Available metrics: cpu, memory, disk, network, process")
    click.echo("  Use 'aiops collector run' to collect data")
