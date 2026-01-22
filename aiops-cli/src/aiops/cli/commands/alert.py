"""
Alert command - Alert management
"""
import sys
import json
import click
from datetime import datetime
from aiops.alerting import AlertManager, AlertRule, Alert, AlertSeverity


@click.group()
def alert():
    """Alert management commands"""
    pass


@alert.command()
@click.option('--name', required=True, help='Alert rule name')
@click.option('--condition', required=True, help='Alert condition')
@click.option('--severity', type=click.Choice(['info', 'warning', 'critical', 'emergency']), default='warning')
@click.option('--description', help='Rule description')
def create(name, condition, severity, description):
    """Create alert rule

    Examples:

        \b
        # Create CPU alert
        aiops alert create --name high_cpu --condition "cpu>90" --severity critical
    """
    try:
        manager = AlertManager()

        rule = AlertRule(
            name=name,
            condition=condition,
            severity=severity,
            description=description,
        )

        manager.create_rule(rule)
        click.echo(f"Alert rule '{name}' created successfully")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@alert.command()
@click.option('--output', type=click.Choice(['table', 'json']), default='table')
def list(output):
    """List alert rules

    Examples:

        \b
        # List all rules
        aiops alert list
    """
    try:
        manager = AlertManager()
        rules = manager.list_rules()

        if output == 'json':
            click.echo(json.dumps(rules, indent=2))
        else:
            if not rules:
                click.echo("No alert rules found")
                return

            click.echo("\nAlert Rules:")
            click.echo("=" * 80)
            for rule in rules:
                status = "✓ Enabled" if rule['enabled'] else "✗ Disabled"
                click.echo(f"\n{rule['name']} [{status}]")
                click.echo(f"  Condition: {rule['condition']}")
                click.echo(f"  Severity: {rule['severity']}")
                if rule.get('description'):
                    click.echo(f"  Description: {rule['description']}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@alert.command()
@click.option('--name', required=True, help='Alert rule name')
def show(name):
    """Show alert rule details

    Examples:

        \b
        # Show rule details
        aiops alert show --name high_cpu
    """
    try:
        manager = AlertManager()
        rule = manager.get_rule(name)

        if not rule:
            click.echo(f"Rule '{name}' not found")
            sys.exit(1)

        click.echo(json.dumps(rule, indent=2))

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@alert.command()
@click.option('--name', required=True, help='Alert rule name')
def delete(name):
    """Delete alert rule

    Examples:

        \b
        # Delete rule
        aiops alert delete --name high_cpu
    """
    try:
        manager = AlertManager()
        manager.delete_rule(name)
        click.echo(f"Alert rule '{name}' deleted")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@alert.command()
@click.option('--name', required=True, help='Alert rule name')
def enable(name):
    """Enable alert rule

    Examples:

        \b
        # Enable rule
        aiops alert enable --name high_cpu
    """
    try:
        manager = AlertManager()
        manager.enable_rule(name)
        click.echo(f"Alert rule '{name}' enabled")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@alert.command()
@click.option('--name', required=True, help='Alert rule name')
def disable(name):
    """Disable alert rule

    Examples:

        \b
        # Disable rule
        aiops alert disable --name high_cpu
    """
    try:
        manager = AlertManager()
        manager.disable_rule(name)
        click.echo(f"Alert rule '{name}' disabled")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@alert.command()
@click.option('--status', help='Filter by status')
@click.option('--severity', help='Filter by severity')
@click.option('--output', type=click.Choice(['table', 'json']), default='table')
def history(status, severity, output):
    """Show alert history

    Examples:

        \b
        # Show all alerts
        aiops alert history

        \b
        # Show firing alerts
        aiops alert history --status firing
    """
    try:
        manager = AlertManager()
        alerts = manager.list_alerts(status=status, severity=severity)

        if output == 'json':
            click.echo(json.dumps(alerts, indent=2))
        else:
            if not alerts:
                click.echo("No alerts found")
                return

            click.echo("\nAlert History:")
            click.echo("=" * 80)
            for alert in alerts:
                click.echo(f"\n{alert['rule_name']} [{alert['status']}]")
                click.echo(f"  Severity: {alert['severity']}")
                click.echo(f"  Message: {alert['message']}")
                click.echo(f"  Started: {alert['started_at']}")
                if alert.get('ended_at'):
                    click.echo(f"  Ended: {alert['ended_at']}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@alert.command()
@click.option('--name', required=True, help='Alert rule name')
@click.option('--user', default='admin', help='User acknowledging the alert')
def acknowledge(name, user):
    """Acknowledge alert

    Examples:

        \b
        # Acknowledge alert
        aiops alert acknowledge --name high_cpu --user ops
    """
    try:
        manager = AlertManager()
        manager.acknowledge_alert(name, user)
        click.echo(f"Alert '{name}' acknowledged by {user}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
