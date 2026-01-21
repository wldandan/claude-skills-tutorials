"""
Config command group - Configuration management commands
"""
import os
import sys
from pathlib import Path
import click
import yaml
from aiops.config import load_config
from aiops.core.exceptions import ConfigurationError


@click.group()
def config():
    """Manage AIOps CLI configuration"""
    pass


@config.command()
@click.option(
    '--config',
    type=click.Path(exists=True),
    help='Path to config file to display (default: use default config)'
)
def show(config):
    """Show current configuration

    Examples:

        \b
        # Show default configuration
        aiops config show

        \b
        # Show specific config file
        aiops config show --config ~/.aiops/config.yaml
    """
    try:
        cfg = load_config(config)

        # Convert config to dict for display
        config_dict = _config_to_dict(cfg)

        # Display as YAML
        output = yaml.safe_dump(config_dict, default_flow_style=False, sort_keys=False)
        click.echo(output)

    except ConfigurationError as e:
        click.echo(f"Configuration error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error reading configuration: {str(e)}", err=True)
        sys.exit(1)


@config.command()
@click.option(
    '--output',
    type=click.Path(),
    default=None,
    help='Output path for config file (default: ~/.aiops/config.yaml)'
)
@click.option(
    '--force',
    is_flag=True,
    help='Overwrite existing config file'
)
def init(output, force):
    """Initialize default configuration file

    Creates a default configuration file at the specified location.

    Examples:

        \b
        # Create config in default location
        aiops config init

        \b
        # Create config in custom location
        aiops config init --output ./my-config.yaml

        \b
        # Overwrite existing config
        aiops config init --force
    """
    # Determine output path
    if output is None:
        config_dir = Path.home() / '.aiops'
        output = config_dir / 'config.yaml'
    else:
        output = Path(output)

    # Check if file exists
    if output.exists() and not force:
        click.echo(f"Configuration file already exists: {output}", err=True)
        click.echo("Use --force to overwrite", err=True)
        sys.exit(1)

    # Create directory if needed
    output.parent.mkdir(parents=True, exist_ok=True)

    # Get default config
    try:
        cfg = load_config(None)
        config_dict = _config_to_dict(cfg)

        # Write to file
        with open(output, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)

        click.echo(f"Configuration file created: {output}")
        click.echo(f"\nEdit this file to customize your settings:")
        click.echo(f"  {output}")

    except Exception as e:
        click.echo(f"Error creating configuration: {str(e)}", err=True)
        sys.exit(1)


@config.command()
@click.argument('key')
@click.argument('value')
@click.option(
    '--config',
    type=click.Path(),
    default=None,
    help='Config file to modify (default: ~/.aiops/config.yaml)'
)
def set(key, value, config):
    """Set configuration value

    Set a configuration value using dot notation for nested keys.

    Examples:

        \b
        # Set CPU threshold
        aiops config set cpu.detection.algorithms.static.threshold_percent 85

        \b
        # Set collection interval
        aiops config set cpu.collection.interval_seconds 2

        \b
        # Modify specific config file
        aiops config set cpu.detection.algorithms.dynamic_baseline.std_multiplier 3.0 \\
            --config ./custom-config.yaml
    """
    # Determine config path
    if config is None:
        config_dir = Path.home() / '.aiops'
        config = config_dir / 'config.yaml'
    else:
        config = Path(config)

    # Check if file exists
    if not config.exists():
        click.echo(f"Configuration file not found: {config}", err=True)
        click.echo("Run 'aiops config init' to create a default config", err=True)
        sys.exit(1)

    try:
        # Load existing config
        with open(config, 'r') as f:
            config_dict = yaml.safe_load(f)

        # Set value using dot notation
        _set_nested_value(config_dict, key, value)

        # Write back to file
        with open(config, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)

        click.echo(f"Configuration updated: {key} = {value}")

    except Exception as e:
        click.echo(f"Error updating configuration: {str(e)}", err=True)
        sys.exit(1)


@config.command()
@click.argument('config_file', type=click.Path(exists=True))
def validate(config_file):
    """Validate configuration file

    Checks if the configuration file is valid and can be loaded.

    Examples:

        \b
        # Validate config file
        aiops config validate ~/.aiops/config.yaml
    """
    try:
        cfg = load_config(config_file)
        click.echo(f"Configuration file is valid: {config_file}")
        click.echo("\nConfiguration summary:")
        click.echo(f"  CPU collection interval: {cfg.cpu.collection.interval_seconds}s")
        click.echo(f"  Static threshold: {cfg.cpu.detection.algorithms.static.threshold_percent}%")
        click.echo(f"  Dynamic std multiplier: {cfg.cpu.detection.algorithms.dynamic_baseline.std_multiplier}")

    except ConfigurationError as e:
        click.echo(f"Configuration validation failed: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error validating configuration: {str(e)}", err=True)
        sys.exit(1)


def _config_to_dict(cfg) -> dict:
    """Convert Config object to dictionary

    Args:
        cfg: Config object

    Returns:
        Dictionary representation
    """
    from dataclasses import asdict
    return asdict(cfg)


def _set_nested_value(data: dict, key: str, value: str):
    """Set nested dictionary value using dot notation

    Args:
        data: Dictionary to modify
        key: Dot-separated key path (e.g., 'cpu.detection.threshold')
        value: Value to set (will be converted to appropriate type)
    """
    keys = key.split('.')
    current = data

    # Navigate to the parent of the target key
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    # Set the value with type conversion
    final_key = keys[-1]
    current[final_key] = _convert_value(value)


def _convert_value(value: str):
    """Convert string value to appropriate type

    Args:
        value: String value

    Returns:
        Converted value (int, float, bool, or str)
    """
    # Try boolean
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'

    # Try int
    try:
        return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Return as string
    return value
