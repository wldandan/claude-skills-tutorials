"""Network statistics collector from psutil."""

import psutil
from datetime import datetime
from typing import List, Optional

from aiops.core import BaseCollector
from aiops.network.models import NetworkMetric
from aiops.core.exceptions import CollectionError


class NetworkStatsCollector(BaseCollector):
    """Collects network interface statistics using psutil."""

    def __init__(self, interfaces: Optional[List[str]] = None):
        """
        Initialize the network stats collector.

        Args:
            interfaces: List of interface names to monitor (e.g., ['eth0', 'wlan0']).
                       If None, monitors all interfaces.
        """
        self.interfaces = interfaces
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the collector."""
        # Verify psutil is available
        try:
            psutil.net_io_counters(pernic=True)
        except Exception as e:
            raise CollectionError(f"Failed to initialize network collector: {str(e)}")

        self._initialized = True

    def collect(self, interface: Optional[str] = None) -> List[NetworkMetric]:
        """
        Collect network interface metrics.

        Args:
            interface: Specific interface to collect (overrides self.interfaces)

        Returns:
            List of NetworkMetric objects
        """
        if not self._initialized:
            raise CollectionError("Collector not initialized")

        try:
            metrics = []
            timestamp = datetime.now()

            # Get per-interface statistics
            net_io = psutil.net_io_counters(pernic=True)

            # Get interface status
            net_if_stats = psutil.net_if_stats()
            net_if_addrs = psutil.net_if_addrs()

            for iface_name, io_counters in net_io.items():
                # Filter interfaces
                if interface:
                    if iface_name != interface:
                        continue
                elif self.interfaces and iface_name not in self.interfaces:
                    continue

                # Skip loopback by default unless explicitly requested
                if not interface and not self.interfaces:
                    if iface_name == 'lo' or iface_name.startswith('lo'):
                        continue

                # Get interface status
                is_up = False
                speed_mbps = 0
                mtu = 1500

                if iface_name in net_if_stats:
                    stats = net_if_stats[iface_name]
                    is_up = stats.isup
                    speed_mbps = stats.speed
                    mtu = stats.mtu

                metric = NetworkMetric(
                    timestamp=timestamp,
                    interface=iface_name,
                    bytes_recv=io_counters.bytes_recv,
                    packets_recv=io_counters.packets_recv,
                    errin=io_counters.errin,
                    dropin=io_counters.dropin,
                    bytes_sent=io_counters.bytes_sent,
                    packets_sent=io_counters.packets_sent,
                    errout=io_counters.errout,
                    dropout=io_counters.dropout,
                    is_up=is_up,
                    speed_mbps=speed_mbps,
                    mtu=mtu,
                )
                metrics.append(metric)

            return metrics

        except Exception as e:
            raise CollectionError(f"Failed to collect network metrics: {str(e)}")

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
