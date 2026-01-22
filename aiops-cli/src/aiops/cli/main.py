"""
AIOps CLI - Main entry point
"""
import sys
import platform
import click
from aiops import __version__


@click.group()
@click.version_option(version=__version__, prog_name="aiops")
@click.pass_context
def cli(ctx):
    """AIOps CLI - Intelligent system monitoring and analysis

    A command-line tool for AI-powered operations, providing real-time
    monitoring, anomaly detection, and root cause analysis.
    """
    # Ensure Click context object exists
    ctx.ensure_object(dict)

    # Check if running on Linux (required for most features)
    if platform.system() != "Linux":
        ctx.obj['non_linux'] = True
    else:
        ctx.obj['non_linux'] = False


@cli.command()
def version():
    """Show version information"""
    click.echo(f"aiops-cli version {__version__}")
    click.echo(f"Python: {sys.version.split()[0]}")
    click.echo(f"Platform: {platform.system()}-{platform.release()}")


# Register command groups
from aiops.cli.commands.collect import collect
from aiops.cli.commands.detect import detect
from aiops.cli.commands.analyze import analyze
from aiops.cli.commands.config import config
from aiops.cli.commands.monitor import monitor

cli.add_command(collect)
cli.add_command(detect)
cli.add_command(analyze)
cli.add_command(config)
cli.add_command(monitor)


def main():
    """Main entry point for the CLI"""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
