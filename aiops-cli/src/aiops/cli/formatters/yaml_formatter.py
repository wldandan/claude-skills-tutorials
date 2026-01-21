"""
YAML formatter for output
"""
import yaml
from typing import Any, List
from datetime import datetime
from aiops.cli.formatters.base import BaseFormatter


class YAMLFormatter(BaseFormatter):
    """Format data as YAML"""

    def __init__(self, default_flow_style: bool = False):
        """Initialize YAML formatter

        Args:
            default_flow_style: Use flow style (compact) if True (default: False)
        """
        self.default_flow_style = default_flow_style

    def format(self, data: Any) -> str:
        """Format data to YAML string

        Args:
            data: Data to format (dict, list, or object with to_dict method)

        Returns:
            YAML string
        """
        formatted_data = self._prepare_data(data)
        return yaml.safe_dump(
            formatted_data,
            default_flow_style=self.default_flow_style,
            allow_unicode=True,
            sort_keys=False
        )

    def _prepare_data(self, data: Any) -> Any:
        """Prepare data for YAML serialization

        Args:
            data: Data to prepare

        Returns:
            YAML-serializable data
        """
        if isinstance(data, list):
            return [self._prepare_data(item) for item in data]
        elif hasattr(data, 'to_dict'):
            return data.to_dict()
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {k: self._prepare_data(v) for k, v in data.items()}
        else:
            return data

    def get_name(self) -> str:
        """Return formatter name

        Returns:
            'yaml'
        """
        return 'yaml'
