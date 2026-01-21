"""
Base formatter for output formatting
"""
from abc import ABC, abstractmethod
from typing import Any, List


class BaseFormatter(ABC):
    """Abstract base class for output formatters"""

    @abstractmethod
    def format(self, data: Any) -> str:
        """Format data to string representation

        Args:
            data: Data to format (CPUMetric, AnomalyEvent, or list of these)

        Returns:
            Formatted string representation
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this formatter

        Returns:
            Formatter name (e.g., 'json', 'yaml', 'table')
        """
        pass


def get_formatter(format_type: str) -> BaseFormatter:
    """Get formatter instance by type

    Args:
        format_type: Type of formatter ('json', 'yaml', 'table')

    Returns:
        Formatter instance

    Raises:
        ValueError: If format_type is not supported
    """
    if format_type == 'json':
        from aiops.cli.formatters.json_formatter import JSONFormatter
        return JSONFormatter()
    elif format_type == 'yaml':
        from aiops.cli.formatters.yaml_formatter import YAMLFormatter
        return YAMLFormatter()
    elif format_type == 'table':
        from aiops.cli.formatters.table import TableFormatter
        return TableFormatter()
    else:
        raise ValueError(f"Unsupported format type: {format_type}")
