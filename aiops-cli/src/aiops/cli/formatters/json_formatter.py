"""
JSON formatter for output
"""
import json
from typing import Any, List
from datetime import datetime
from aiops.cli.formatters.base import BaseFormatter


class JSONFormatter(BaseFormatter):
    """Format data as JSON"""

    def __init__(self, indent: int = 2):
        """Initialize JSON formatter

        Args:
            indent: Number of spaces for indentation (default: 2)
        """
        self.indent = indent

    def format(self, data: Any) -> str:
        """Format data to JSON string

        Args:
            data: Data to format (dict, list, or object with to_dict method)

        Returns:
            JSON string
        """
        formatted_data = self._prepare_data(data)
        return json.dumps(formatted_data, indent=self.indent, ensure_ascii=False)

    def _prepare_data(self, data: Any) -> Any:
        """Prepare data for JSON serialization

        Args:
            data: Data to prepare

        Returns:
            JSON-serializable data
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
            'json'
        """
        return 'json'
