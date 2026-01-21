"""Network interface metrics data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any


@dataclass
class NetworkMetric:
    """Network interface metrics from /proc/net/dev and psutil."""

    timestamp: datetime
    interface: str

    # Receive statistics
    bytes_recv: int
    packets_recv: int
    errin: int
    dropin: int

    # Transmit statistics
    bytes_sent: int
    packets_sent: int
    errout: int
    dropout: int

    # Interface status
    is_up: bool = True
    speed_mbps: int = 0  # Interface speed in Mbps
    mtu: int = 1500

    def __post_init__(self):
        """Validate network metric."""
        if not self.interface:
            raise ValueError("Interface name cannot be empty")

        if self.bytes_recv < 0:
            raise ValueError("bytes_recv must be non-negative")

        if self.bytes_sent < 0:
            raise ValueError("bytes_sent must be non-negative")

        if self.packets_recv < 0:
            raise ValueError("packets_recv must be non-negative")

        if self.packets_sent < 0:
            raise ValueError("packets_sent must be non-negative")

    @property
    def total_bytes(self) -> int:
        """Total bytes (recv + sent)."""
        return self.bytes_recv + self.bytes_sent

    @property
    def total_packets(self) -> int:
        """Total packets (recv + sent)."""
        return self.packets_recv + self.packets_sent

    @property
    def total_errors(self) -> int:
        """Total errors (recv + sent)."""
        return self.errin + self.errout

    @property
    def total_drops(self) -> int:
        """Total drops (recv + sent)."""
        return self.dropin + self.dropout

    @property
    def bytes_recv_mb(self) -> float:
        """Bytes received in MB."""
        return self.bytes_recv / (1024 * 1024)

    @property
    def bytes_sent_mb(self) -> float:
        """Bytes sent in MB."""
        return self.bytes_sent / (1024 * 1024)

    @property
    def total_bytes_mb(self) -> float:
        """Total bytes in MB."""
        return self.total_bytes / (1024 * 1024)

    @property
    def error_rate_recv(self) -> float:
        """Receive error rate (errors per packet)."""
        if self.packets_recv == 0:
            return 0.0
        return self.errin / self.packets_recv

    @property
    def error_rate_sent(self) -> float:
        """Send error rate (errors per packet)."""
        if self.packets_sent == 0:
            return 0.0
        return self.errout / self.packets_sent

    @property
    def drop_rate_recv(self) -> float:
        """Receive drop rate (drops per packet)."""
        if self.packets_recv == 0:
            return 0.0
        return self.dropin / self.packets_recv

    @property
    def drop_rate_sent(self) -> float:
        """Send drop rate (drops per packet)."""
        if self.packets_sent == 0:
            return 0.0
        return self.dropout / self.packets_sent

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'interface': self.interface,
            'bytes_recv': self.bytes_recv,
            'packets_recv': self.packets_recv,
            'errin': self.errin,
            'dropin': self.dropin,
            'bytes_sent': self.bytes_sent,
            'packets_sent': self.packets_sent,
            'errout': self.errout,
            'dropout': self.dropout,
            'is_up': self.is_up,
            'speed_mbps': self.speed_mbps,
            'mtu': self.mtu,
            'total_bytes': self.total_bytes,
            'total_packets': self.total_packets,
            'total_errors': self.total_errors,
            'total_drops': self.total_drops,
            'bytes_recv_mb': self.bytes_recv_mb,
            'bytes_sent_mb': self.bytes_sent_mb,
            'total_bytes_mb': self.total_bytes_mb,
            'error_rate_recv': self.error_rate_recv,
            'error_rate_sent': self.error_rate_sent,
            'drop_rate_recv': self.drop_rate_recv,
            'drop_rate_sent': self.drop_rate_sent,
        }
