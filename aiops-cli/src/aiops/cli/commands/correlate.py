"""
Correlate command - Correlation analysis
"""
import sys
import json
import click
from aiops.correlation import CorrelationAnalyzer


@click.command()
@click.option(
    '--metrics',
    type=str,
    required=True,
    help='Metrics to correlate (comma-separated)'
)
@click.option(
    '--data',
    type=click.Path(exists=True),
    required=True,
    help='JSON file with metrics data'
)
@click.option(
    '--threshold',
    type=float,
    default=0.7,
    help='Correlation threshold (default: 0.7)'
)
@click.option(
    '--output',
    type=click.Choice(['table', 'json'], case_sensitive=False),
    default='table',
    help='Output format'
)
def correlate(metrics, data, threshold, output):
    """Analyze metric correlations

    Examples:

        \b
        # Analyze correlations
        aiops correlate --metrics cpu,memory --data metrics.json
    """
    try:
        # Load data
        with open(data, 'r') as f:
            metrics_data = json.load(f)

        # Parse metrics
        metric_names = [m.strip() for m in metrics.split(',')]

        # Filter data
        filtered_data = {k: v for k, v in metrics_data.items() if k in metric_names}

        if not filtered_data:
            click.echo("No matching metrics found in data")
            sys.exit(1)

        # Analyze correlations
        analyzer = CorrelationAnalyzer()
        results = analyzer.find_correlations(filtered_data, threshold)

        if output == 'json':
            click.echo(json.dumps(results, indent=2))
        else:
            click.echo("\nCorrelation Analysis Results:")
            click.echo("=" * 80)
            for i, result in enumerate(results, 1):
                click.echo(f"\n{i}. {result['metric1']} <-> {result['metric2']}")
                click.echo(f"   Correlation: {result['correlation']:.3f}")
                click.echo(f"   P-value: {result['p_value']:.4f}")
                click.echo(f"   Strength: {result['strength']}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
