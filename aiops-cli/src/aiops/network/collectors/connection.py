"""Network connection collector from psutil."""

import psutil
from datetime import datetime
from typing import List, Optional, Dict
from collections import Counter

from aiops.core import BaseCollector
from aiops.network.models import ConnectionMetric
from aiops.core.exceptions import CollectionError


class ConnectionCollector(BaseCollector):
    """Collects network connection statistics using psutil."""

    def __init__(self, kind: str = 'inet', include_listening: bool = True):
        """
        Initialize the connection collector.

        Args:
            kind: Connection kind ('inet', 'inet4', 'inet6', 'tcp', 'tcp4', 'tcp6', 'udp', 'udp4', 'udp6', 'unix', 'all')
            include_listening: Include listening connections
        """
        self.kind = kind
        self.include_listening = include_listening
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the collector."""
        # Verify psutil is available
        try:
            psutil.net_connections(kind=self.kind)
        except Exception as e:
            raise CollectionError(f"Failed to initialize connection collector: {str(e)}")

        self._initialized = True

    def collect(self, pid: Optional[int] = None) -> List[ConnectionMetric]:
        """
        Collect network connection metrics.

        Args:
            pid: Specific process ID to collect connections for

        Returns:
            List of ConnectionMetric objects
        """
        if not self._initialized:
            raise CollectionError("Collector not initialized")

        try:
            metrics = []
            timestamp = datetime.now()

            # Get connections
            if pid:
                try:
                    proc = psutil.Process(pid)
                    connections = proc.connections(kind=self.kind)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return []
            else:
                connections = psutil.net_connections(kind=self.kind)

            for conn in connections:
                # Skip if not including listening and connection is listening
                if not self.include_listening and conn.status == 'LISTEN':
                    continue

                # Parse local address
                local_addr = conn.laddr.ip if conn.laddr else '0.0.0.0'
                local_port = conn.laddr.port if conn.laddr else 0

                # Parse remote address
                remote_addr = conn.raddr.ip if conn.raddr else '0.0.0.0'
                remote_port = conn.raddr.port if conn.raddr else 0

                # Determine protocol
                protocol = self._get_protocol(conn)

                # Determine family
                family = 'AF_INET6' if conn.family == psutil.AF_INET6 else 'AF_INET'

                # Get process info
                process_pid = conn.pid if hasattr(conn, 'pid') else None
                process_name = None
                if process_pid:
                    try:
                        proc = psutil.Process(process_pid)
                        process_name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                metric = ConnectionMetric(
                    timestamp=timestamp,
                    protocol=protocol,
                    local_address=local_addr,
                    local_port=local_port,
                    remote_address=remote_addr,
                    remote_port=remote_port,
                    status=conn.status,
                    pid=process_pid,
                    process_name=process_name,
                    fd=conn.fd if hasattr(conn, 'fd') else None,
                    family=family,
                )
                metrics.append(metric)

            return metrics

        except Exception as e:
            raise CollectionError(f"Failed to collect connection metrics: {str(e)}")

    def get_connection_stats(self) -> Dict[str, int]:
        """
        Get connection statistics summary.

        Returns:
            Dictionary with connection counts by status
        """
        if not self._initialized:
            raise CollectionError("Collector not initialized")

        try:
            connections = psutil.net_connections(kind=self.kind)
            status_counts = Counter(conn.status for conn in connections)
            return dict(status_counts)
        except Exception as e:
            raise CollectionError(f"Failed to get connection stats: {str(e)}")

    def _get_protocol(self, conn) -> str:
        """
        Determine protocol from connection.

        Args:
            conn: psutil connection object

        Returns:
            Protocol string ('tcp', 'udp', 'tcp6', 'udp6')
        """
        is_ipv6 = conn.family == psutil.AF_INET6

        if conn.type == psutil.SOCK_STREAM:
            return 'tcp6' if is_ipv6 else 'tcp'
        elif conn.type == psutil.SOCK_DGRAM:
            return 'udp6' if is_ipv6 else 'udp'
        else:
            return 'tcp6' if is_ipv6 else 'tcp'

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
