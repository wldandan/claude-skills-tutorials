"""
Table formatter for output using Rich library
"""
from typing import Any, List
from rich.console import Console
from rich.table import Table
from rich.text import Text
from aiops.cli.formatters.base import BaseFormatter
from aiops.cpu.models.cpu_metric import CPUMetric
from aiops.cpu.models.anomaly_event import AnomalyEvent
from aiops.cpu.models.process_metric import ProcessMetric
from aiops.memory.models import MemoryMetric, ProcessMemoryMetric
from aiops.diskio.models import DiskIOMetric, ProcessIOMetric


class TableFormatter(BaseFormatter):
    """Format data as beautiful terminal tables"""

    def __init__(self, colors: bool = True):
        """Initialize table formatter

        Args:
            colors: Enable color output (default: True)
        """
        self.console = Console(color_system="auto" if colors else None)
        self.colors = colors

    def format(self, data: Any) -> str:
        """Format data to table string

        Args:
            data: Data to format (CPUMetric, AnomalyEvent, ProcessMetric, or lists)

        Returns:
            Formatted table string
        """
        if not data:
            return "No data to display"

        # Determine data type
        if isinstance(data, list):
            if len(data) == 0:
                return "No data to display"
            sample = data[0]
        else:
            sample = data
            data = [data]

        # Format based on type
        if isinstance(sample, CPUMetric):
            return self._format_cpu_metrics(data)
        elif isinstance(sample, MemoryMetric):
            return self._format_memory_metrics(data)
        elif isinstance(sample, DiskIOMetric):
            return self._format_diskio_metrics(data)
        elif isinstance(sample, AnomalyEvent):
            return self._format_anomaly_events(data)
        elif isinstance(sample, ProcessMetric):
            return self._format_process_metrics(data)
        elif isinstance(sample, ProcessMemoryMetric):
            return self._format_process_memory_metrics(data)
        elif isinstance(sample, ProcessIOMetric):
            return self._format_process_io_metrics(data)
        elif isinstance(sample, dict):
            # Handle dict with memory_metrics and process_metrics keys
            if 'memory_metrics' in sample and 'process_metrics' in sample:
                return self._format_memory_with_processes(sample)
            elif 'cpu_metrics' in sample and 'process_metrics' in sample:
                return self._format_cpu_with_processes(sample)
            elif 'diskio_metrics' in sample and 'process_metrics' in sample:
                return self._format_diskio_with_processes(sample)
            # Generic dict formatting
            return self._format_dicts(data)
        else:
            return str(data)

    def _format_cpu_metrics(self, metrics: List[CPUMetric]) -> str:
        """Format CPU metrics as table

        Args:
            metrics: List of CPUMetric objects

        Returns:
            Formatted table string
        """
        table = Table(title="CPU Metrics", show_header=True, header_style="bold cyan")
        table.add_column("Timestamp", style="dim", width=20)
        table.add_column("CPU%", justify="right")
        table.add_column("User%", justify="right")
        table.add_column("System%", justify="right")
        table.add_column("Idle%", justify="right")
        table.add_column("IOWait%", justify="right")

        for metric in metrics:
            # Color code CPU% based on value
            cpu_style = self._get_cpu_style(metric.cpu_percent)

            table.add_row(
                metric.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                Text(f"{metric.cpu_percent:.1f}", style=cpu_style),
                f"{metric.cpu_user:.1f}",
                f"{metric.cpu_system:.1f}",
                f"{metric.cpu_idle:.1f}",
                f"{metric.cpu_iowait:.1f}",
            )

        # Capture table output
        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    def _format_anomaly_events(self, events: List[AnomalyEvent]) -> str:
        """Format anomaly events as table

        Args:
            events: List of AnomalyEvent objects

        Returns:
            Formatted table string
        """
        table = Table(title="Anomaly Events", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=12)
        table.add_column("Timestamp", width=20)
        table.add_column("Severity", width=10)
        table.add_column("Type", width=20)
        table.add_column("Confidence", justify="right")
        table.add_column("Avg CPU%", justify="right")
        table.add_column("Max CPU%", justify="right")
        table.add_column("Algorithm", width=15)

        for event in events:
            # Color code severity
            severity_style = self._get_severity_style(event.severity)
            confidence_style = self._get_confidence_style(event.confidence)

            avg_cpu = event.metrics.get('avg_cpu_percent', 0)
            max_cpu = event.metrics.get('max_cpu_percent', 0)

            table.add_row(
                event.id[:8],
                event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                Text(event.severity.upper(), style=severity_style),
                event.type,
                Text(f"{event.confidence:.2f}", style=confidence_style),
                f"{avg_cpu:.1f}",
                f"{max_cpu:.1f}",
                event.algorithm,
            )

        # Capture table output
        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    def _format_process_metrics(self, processes: List[ProcessMetric]) -> str:
        """Format process metrics as table

        Args:
            processes: List of ProcessMetric objects

        Returns:
            Formatted table string
        """
        table = Table(title="Process Metrics", show_header=True, header_style="bold cyan")
        table.add_column("PID", justify="right", width=8)
        table.add_column("Name", width=25)
        table.add_column("CPU%", justify="right")
        table.add_column("Memory%", justify="right")
        table.add_column("Threads", justify="right")
        table.add_column("Status", width=8)
        table.add_column("User", width=15)

        for proc in processes:
            cpu_style = self._get_cpu_style(proc.cpu_percent)

            table.add_row(
                str(proc.pid),
                proc.name[:25],
                Text(f"{proc.cpu_percent:.1f}", style=cpu_style),
                f"{proc.memory_percent:.1f}",
                str(proc.num_threads),
                proc.status,
                proc.username[:15] if proc.username else "N/A",
            )

        # Capture table output
        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    def _format_memory_metrics(self, metrics: List[MemoryMetric]) -> str:
        """Format memory metrics as table

        Args:
            metrics: List of MemoryMetric objects

        Returns:
            Formatted table string
        """
        table = Table(title="Memory Metrics", show_header=True, header_style="bold cyan")
        table.add_column("Timestamp", style="dim", width=20)
        table.add_column("Used%", justify="right")
        table.add_column("Available%", justify="right")
        table.add_column("Used (GB)", justify="right")
        table.add_column("Available (GB)", justify="right")
        table.add_column("Swap%", justify="right")
        table.add_column("Cached (GB)", justify="right")

        for metric in metrics:
            # Color code memory% based on value
            mem_style = self._get_memory_style(metric.mem_used_percent)
            swap_style = self._get_memory_style(metric.swap_used_percent)

            table.add_row(
                metric.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                Text(f"{metric.mem_used_percent:.1f}", style=mem_style),
                f"{metric.mem_available_percent:.1f}",
                f"{metric.mem_used / (1024**3):.2f}",
                f"{metric.mem_available / (1024**3):.2f}",
                Text(f"{metric.swap_used_percent:.1f}", style=swap_style),
                f"{metric.cached / (1024**3):.2f}",
            )

        # Capture table output
        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    def _format_process_memory_metrics(self, processes: List[ProcessMemoryMetric]) -> str:
        """Format process memory metrics as table

        Args:
            processes: List of ProcessMemoryMetric objects

        Returns:
            Formatted table string
        """
        table = Table(title="Process Memory Metrics", show_header=True, header_style="bold cyan")
        table.add_column("PID", justify="right", width=8)
        table.add_column("Name", width=25)
        table.add_column("RSS (MB)", justify="right")
        table.add_column("VMS (MB)", justify="right")
        table.add_column("Swap (MB)", justify="right")
        table.add_column("Status", width=8)
        table.add_column("User", width=15)

        for proc in processes:
            table.add_row(
                str(proc.pid),
                proc.name[:25],
                f"{proc.rss_mb:.1f}",
                f"{proc.vms_mb:.1f}",
                f"{proc.swap_mb:.1f}",
                proc.status,
                proc.username[:15] if proc.username else "N/A",
            )

        # Capture table output
        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    def _format_memory_with_processes(self, data: dict) -> str:
        """Format memory metrics with process information

        Args:
            data: Dict with 'memory_metrics' and 'process_metrics' keys

        Returns:
            Formatted table string
        """
        output = []

        # Format memory metrics
        memory_metrics = data.get('memory_metrics', [])
        if memory_metrics:
            output.append(self._format_memory_metrics(memory_metrics))

        # Format process metrics
        process_metrics = data.get('process_metrics', [])
        if process_metrics:
            output.append("\n")
            output.append(self._format_process_memory_metrics(process_metrics))

        return "".join(output)

    def _format_cpu_with_processes(self, data: dict) -> str:
        """Format CPU metrics with process information

        Args:
            data: Dict with 'cpu_metrics' and 'process_metrics' keys

        Returns:
            Formatted table string
        """
        output = []

        # Format CPU metrics
        cpu_metrics = data.get('cpu_metrics', [])
        if cpu_metrics:
            output.append(self._format_cpu_metrics(cpu_metrics))

        # Format process metrics
        process_metrics = data.get('process_metrics', [])
        if process_metrics:
            output.append("\n")
            output.append(self._format_process_metrics(process_metrics))

        return "".join(output)

    def _format_dicts(self, data: List[dict]) -> str:
        """Format generic dicts as table

        Args:
            data: List of dictionaries

        Returns:
            Formatted table string
        """
        if not data:
            return "No data to display"

        # Get all keys from first dict
        keys = list(data[0].keys())

        table = Table(show_header=True, header_style="bold cyan")
        for key in keys:
            table.add_column(str(key))

        for item in data:
            table.add_row(*[str(item.get(k, "N/A")) for k in keys])

        # Capture table output
        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    def _get_cpu_style(self, cpu_percent: float) -> str:
        """Get style for CPU percentage

        Args:
            cpu_percent: CPU percentage value

        Returns:
            Rich style string
        """
        if not self.colors:
            return ""

        if cpu_percent >= 95:
            return "bold red"
        elif cpu_percent >= 80:
            return "yellow"
        elif cpu_percent >= 60:
            return "cyan"
        else:
            return "green"

    def _get_severity_style(self, severity: str) -> str:
        """Get style for severity level

        Args:
            severity: Severity level (warning, critical, emergency)

        Returns:
            Rich style string
        """
        if not self.colors:
            return ""

        severity_map = {
            'warning': 'yellow',
            'critical': 'bold yellow',
            'emergency': 'bold red'
        }
        return severity_map.get(severity.lower(), 'white')

    def _get_confidence_style(self, confidence: float) -> str:
        """Get style for confidence level

        Args:
            confidence: Confidence value (0.0-1.0)

        Returns:
            Rich style string
        """
        if not self.colors:
            return ""

        if confidence >= 0.9:
            return "bold green"
        elif confidence >= 0.7:
            return "green"
        elif confidence >= 0.5:
            return "yellow"
        else:
            return "red"

    def _get_memory_style(self, memory_percent: float) -> str:
        """Get style for memory percentage

        Args:
            memory_percent: Memory percentage value

        Returns:
            Rich style string
        """
        if not self.colors:
            return ""

        if memory_percent >= 90:
            return "bold red"
        elif memory_percent >= 80:
            return "yellow"
        elif memory_percent >= 60:
            return "cyan"
        else:
            return "green"

    def get_name(self) -> str:
        """Return formatter name

        Returns:
            'table'
        """
        return 'table'

    def _format_diskio_metrics(self, metrics: List[DiskIOMetric]) -> str:
        """Format disk I/O metrics as table

        Args:
            metrics: List of DiskIOMetric objects

        Returns:
            Formatted table string
        """
        table = Table(title="Disk I/O Metrics", show_header=True, header_style="bold cyan")
        table.add_column("Timestamp", style="dim", width=20)
        table.add_column("Device", width=12)
        table.add_column("Read (MB)", justify="right")
        table.add_column("Write (MB)", justify="right")
        table.add_column("IOPS", justify="right")
        table.add_column("Avg Read (ms)", justify="right")
        table.add_column("Avg Write (ms)", justify="right")
        table.add_column("Queue", justify="right")

        for metric in metrics:
            read_mb = metric.read_bytes / (1024 * 1024)
            write_mb = metric.write_bytes / (1024 * 1024)

            table.add_row(
                metric.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                metric.device,
                f"{read_mb:.2f}",
                f"{write_mb:.2f}",
                str(metric.total_io_operations),
                f"{metric.avg_read_time_ms:.2f}",
                f"{metric.avg_write_time_ms:.2f}",
                str(metric.io_in_progress),
            )

        # Capture table output
        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    def _format_process_io_metrics(self, processes: List[ProcessIOMetric]) -> str:
        """Format process I/O metrics as table

        Args:
            processes: List of ProcessIOMetric objects

        Returns:
            Formatted table string
        """
        table = Table(title="Process I/O Metrics", show_header=True, header_style="bold cyan")
        table.add_column("PID", justify="right", width=8)
        table.add_column("Name", width=25)
        table.add_column("Read (MB)", justify="right")
        table.add_column("Write (MB)", justify="right")
        table.add_column("Total (MB)", justify="right")
        table.add_column("Read Calls", justify="right")
        table.add_column("Write Calls", justify="right")
        table.add_column("User", width=15)

        for proc in processes:
            table.add_row(
                str(proc.pid),
                proc.name[:25],
                f"{proc.read_bytes_mb:.2f}",
                f"{proc.write_bytes_mb:.2f}",
                f"{proc.total_io_mb:.2f}",
                str(proc.syscr),
                str(proc.syscw),
                proc.username[:15] if proc.username else "N/A",
            )

        # Capture table output
        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    def _format_diskio_with_processes(self, data: dict) -> str:
        """Format disk I/O metrics with process information

        Args:
            data: Dict with 'diskio_metrics' and 'process_metrics' keys

        Returns:
            Formatted table string
        """
        output = []

        # Format disk I/O metrics
        diskio_metrics = data.get('diskio_metrics', [])
        if diskio_metrics:
            output.append(self._format_diskio_metrics(diskio_metrics))

        # Format process metrics
        process_metrics = data.get('process_metrics', [])
        if process_metrics:
            output.append("\n")
            output.append(self._format_process_io_metrics(process_metrics))

        return "".join(output)
