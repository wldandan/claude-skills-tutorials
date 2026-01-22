"""
RCA command - Root cause analysis
"""
import sys
import json
import click
from aiops.rca import RootCauseAnalyzer


@click.command()
@click.option(
    '--events',
    type=click.Path(exists=True),
    required=True,
    help='JSON file with anomaly events'
)
@click.option(
    '--metrics',
    type=click.Path(exists=True),
    help='Optional JSON file with metrics data'
)
@click.option(
    '--output',
    type=click.Choice(['table', 'json'], case_sensitive=False),
    default='table',
    help='Output format'
)
def rca(events, metrics, output):
    """Root cause analysis

    Examples:

        \b
        # Analyze root cause
        aiops rca --events anomalies.json
    """
    try:
        # Load events
        with open(events, 'r') as f:
            events_data = json.load(f)

        # Load metrics if provided
        metrics_data = None
        if metrics:
            with open(metrics, 'r') as f:
                metrics_data = json.load(f)

        # Convert to simple objects for analysis
        class SimpleEvent:
            def __init__(self, data):
                self.type = data.get('type', 'unknown')
                self.severity = data.get('severity', 'warning')
                self.confidence = data.get('confidence', 0.5)
                self.metrics = data.get('metrics', {})
                from datetime import datetime
                self.timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))

        anomaly_events = [SimpleEvent(e) for e in events_data]

        # Analyze
        analyzer = RootCauseAnalyzer()
        result = analyzer.analyze(anomaly_events, metrics_data)

        if output == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo("\nRoot Cause Analysis:")
            click.echo("=" * 80)
            click.echo(f"\nRoot Cause: {result['root_cause']}")
            click.echo(f"Confidence: {result['confidence']:.2%}")
            click.echo(f"Anomaly Count: {result['anomaly_count']}")

            click.echo("\nAnomaly Distribution:")
            for atype, count in result['anomaly_distribution'].items():
                click.echo(f"  - {atype}: {count}")

            click.echo("\nRecommendations:")
            for i, rec in enumerate(result['recommendations'], 1):
                click.echo(f"  {i}. {rec}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
