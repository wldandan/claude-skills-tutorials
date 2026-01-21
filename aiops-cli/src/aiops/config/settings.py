"""Configuration management module."""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CPUCollectionConfig:
    """CPU collection configuration."""
    interval_seconds: int = 1
    process_interval: int = 5
    max_processes: int = 50


@dataclass
class StaticDetectionConfig:
    """Static threshold detection configuration."""
    enabled: bool = True
    threshold_percent: float = 80.0
    duration_seconds: int = 300


@dataclass
class DynamicBaselineConfig:
    """Dynamic baseline detection configuration."""
    enabled: bool = True
    window_days: int = 7
    std_multiplier: float = 2.0


@dataclass
class TimeSeriesDetectionConfig:
    """Time series detection configuration."""
    enabled: bool = False
    algorithm: str = "isolation_forest"
    contamination: float = 0.05


@dataclass
class DetectionAlgorithmsConfig:
    """Detection algorithms configuration."""
    static: StaticDetectionConfig = field(default_factory=StaticDetectionConfig)
    dynamic_baseline: DynamicBaselineConfig = field(
        default_factory=DynamicBaselineConfig
    )
    time_series: TimeSeriesDetectionConfig = field(
        default_factory=TimeSeriesDetectionConfig
    )


@dataclass
class StorageConfig:
    """Storage configuration."""
    backend: str = "sqlite"
    path: str = "/var/lib/aiops/cpu.db"
    retention_days: int = 30


@dataclass
class AlertingConfig:
    """Alerting configuration."""
    enabled: bool = False
    consecutive_periods: int = 3


@dataclass
class OutputConfig:
    """Output configuration."""
    default_format: str = "table"  # table, json, yaml
    colors: bool = True


@dataclass
class CPUConfig:
    """CPU feature configuration."""
    collection: CPUCollectionConfig = field(default_factory=CPUCollectionConfig)
    detection: DetectionAlgorithmsConfig = field(
        default_factory=DetectionAlgorithmsConfig
    )
    storage: StorageConfig = field(default_factory=StorageConfig)
    alerting: AlertingConfig = field(default_factory=AlertingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


@dataclass
class MemoryCollectionConfig:
    """Memory collection configuration."""
    interval_seconds: int = 1
    process_interval: int = 5
    max_processes: int = 50


@dataclass
class MemoryLeakDetectionConfig:
    """Memory leak detection configuration."""
    enabled: bool = True
    min_samples: int = 100
    growth_threshold_mb: float = 50.0
    confidence_threshold: float = 0.8


@dataclass
class OOMDetectionConfig:
    """OOM risk detection configuration."""
    enabled: bool = True
    prediction_window_hours: int = 24
    risk_threshold_percent: float = 90.0


@dataclass
class SwapDetectionConfig:
    """Swap anomaly detection configuration."""
    enabled: bool = True
    threshold_percent: float = 10.0
    spike_multiplier: float = 2.0


@dataclass
class MemoryDetectionAlgorithmsConfig:
    """Memory detection algorithms configuration."""
    memory_leak: MemoryLeakDetectionConfig = field(default_factory=MemoryLeakDetectionConfig)
    oom_risk: OOMDetectionConfig = field(default_factory=OOMDetectionConfig)
    swap_anomaly: SwapDetectionConfig = field(default_factory=SwapDetectionConfig)


@dataclass
class MemoryConfig:
    """Memory feature configuration."""
    collection: MemoryCollectionConfig = field(default_factory=MemoryCollectionConfig)
    detection: MemoryDetectionAlgorithmsConfig = field(default_factory=MemoryDetectionAlgorithmsConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    alerting: AlertingConfig = field(default_factory=AlertingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


@dataclass
class Config:
    """Main configuration class."""
    cpu: CPUConfig = field(default_factory=CPUConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        cpu_data = data.get("cpu", {})
        memory_data = data.get("memory", {})

        # Parse CPU config
        cpu_collection_data = cpu_data.get("collection", {})
        cpu_detection_data = cpu_data.get("detection", {})
        cpu_algorithms_data = cpu_detection_data.get("algorithms", {})
        cpu_storage_data = cpu_data.get("storage", {})
        cpu_alerting_data = cpu_data.get("alerting", {})
        cpu_output_data = cpu_data.get("output", {})

        cpu_static_data = cpu_algorithms_data.get("static", {})
        cpu_dynamic_data = cpu_algorithms_data.get("dynamic_baseline", {})
        cpu_timeseries_data = cpu_algorithms_data.get("time_series", {})

        # Parse Memory config
        memory_collection_data = memory_data.get("collection", {})
        memory_detection_data = memory_data.get("detection", {})
        memory_algorithms_data = memory_detection_data.get("algorithms", {})
        memory_storage_data = memory_data.get("storage", {})
        memory_alerting_data = memory_data.get("alerting", {})
        memory_output_data = memory_data.get("output", {})

        memory_leak_data = memory_algorithms_data.get("memory_leak", {})
        oom_risk_data = memory_algorithms_data.get("oom_risk", {})
        swap_anomaly_data = memory_algorithms_data.get("swap_anomaly", {})

        return cls(
            cpu=CPUConfig(
                collection=CPUCollectionConfig(**cpu_collection_data),
                detection=DetectionAlgorithmsConfig(
                    static=StaticDetectionConfig(**cpu_static_data),
                    dynamic_baseline=DynamicBaselineConfig(**cpu_dynamic_data),
                    time_series=TimeSeriesDetectionConfig(**cpu_timeseries_data),
                ),
                storage=StorageConfig(**cpu_storage_data),
                alerting=AlertingConfig(**cpu_alerting_data),
                output=OutputConfig(**cpu_output_data),
            ),
            memory=MemoryConfig(
                collection=MemoryCollectionConfig(**memory_collection_data),
                detection=MemoryDetectionAlgorithmsConfig(
                    memory_leak=MemoryLeakDetectionConfig(**memory_leak_data),
                    oom_risk=OOMDetectionConfig(**oom_risk_data),
                    swap_anomaly=SwapDetectionConfig(**swap_anomaly_data),
                ),
                storage=StorageConfig(**memory_storage_data),
                alerting=AlertingConfig(**memory_alerting_data),
                output=OutputConfig(**memory_output_data),
            )
        )


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses default config.

    Returns:
        Config object
    """
    if config_path is None:
        # Use default config
        config_path = (
            Path(__file__).parent / "default_config.yaml"
        )

    # Override with environment variable if set
    env_config_path = os.environ.get("AIOPS_CONFIG")
    if env_config_path:
        config_path = Path(env_config_path)

    if config_path.exists():
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
            return Config.from_dict(data or {})

    return Config()
