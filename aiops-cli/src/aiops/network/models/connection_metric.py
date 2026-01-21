"""Network connection metrics data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class ConnectionMetric:
    """Network connection metrics from /proc/net/tcp, /proc/net/udp, and psutil."""

    timestamp: datetime
    protocol: str  # 'tcp', 'udp', 'tcp6', 'udp6'
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    status: str  # 'ESTABLISHED', 'LISTEN', 'TIME_WAIT', 'CLOSE_WAIT', etc.

    # Process information
    pid: Optional[int] = None
    process_name: Optional[str] = None

    # Additional metadata
    fd: Optional[int] = None  # File descriptor
    family: str = 'AF_INET'  # 'AF_INET' or 'AF_INET6'

    def __post_init__(self):
        """Validate connection metric."""
        valid_protocols = ['tcp', 'udp', 'tcp6', 'udp6']
        if self.protocol not in valid_protocols:
            raise ValueError(
                f"Invalid protocol: {self.protocol}. Must be one of {valid_protocols}"
            )

        if self.local_port < 0 or self.local_port > 65535:
            raise ValueError(f"Invalid local_port: {self.local_port}")

        if self.remote_port < 0 or self.remote_port > 65535:
            raise ValueError(f"Invalid remote_port: {self.remote_port}")

        # Validate TCP status
        if self.protocol in ['tcp', 'tcp6']:
            valid_tcp_states = [
                'ESTABLISHED', 'SYN_SENT', 'SYN_RECV', 'FIN_WAIT1', 'FIN_WAIT2',
                'TIME_WAIT', 'CLOSE', 'CLOSE_WAIT', 'LAST_ACK', 'LISTEN',
                'CLOSING', 'NONE'
            ]
            if self.status not in valid_tcp_states:
                raise ValueError(
                    f"Invalid TCP status: {self.status}. Must be one of {valid_tcp_states}"
                )

    @property
    def is_listening(self) -> bool:
        """Check if connection is in LISTEN state."""
        return self.status == 'LISTEN'

    @property
    def is_established(self) -> bool:
        """Check if connection is ESTABLISHED."""
        return self.status == 'ESTABLISHED'

    @property
    def is_time_wait(self) -> bool:
        """Check if connection is in TIME_WAIT state."""
        return self.status == 'TIME_WAIT'

    @property
    def is_close_wait(self) -> bool:
        """Check if connection is in CLOSE_WAIT state."""
        return self.status == 'CLOSE_WAIT'

    @property
    def local_endpoint(self) -> str:
        """Local endpoint as 'address:port'."""
        return f"{self.local_address}:{self.local_port}"

    @property
    def remote_endpoint(self) -> str:
        """Remote endpoint as 'address:port'."""
        return f"{self.remote_address}:{self.remote_port}"

    @property
    def connection_tuple(self) -> str:
        """Connection as 'local -> remote'."""
        return f"{self.local_endpoint} -> {self.remote_endpoint}"

    @property
    def is_ipv6(self) -> bool:
        """Check if connection is IPv6."""
        return self.protocol in ['tcp6', 'udp6'] or self.family == 'AF_INET6'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'protocol': self.protocol,
            'local_address': self.local_address,
            'local_port': self.local_port,
            'remote_address': self.remote_address,
            'remote_port': self.remote_port,
            'status': self.status,
            'pid': self.pid,
            'process_name': self.process_name,
            'fd': self.fd,
            'family': self.family,
            'is_listening': self.is_listening,
            'is_established': self.is_established,
            'is_time_wait': self.is_time_wait,
            'is_close_wait': self.is_close_wait,
            'local_endpoint': self.local_endpoint,
            'remote_endpoint': self.remote_endpoint,
            'connection_tuple': self.connection_tuple,
            'is_ipv6': self.is_ipv6,
        }
