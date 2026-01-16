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
class Config:
    """Main configuration class."""
    cpu: CPUConfig = field(default_factory=CPUConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        cpu_data = data.get("cpu", {})

        collection_data = cpu_data.get("collection", {})
        detection_data = cpu_data.get("detection", {})
        algorithms_data = detection_data.get("algorithms", {})
        storage_data = cpu_data.get("storage", {})
        alerting_data = cpu_data.get("alerting", {})
        output_data = cpu_data.get("output", {})

        static_data = algorithms_data.get("static", {})
        dynamic_data = algorithms_data.get("dynamic_baseline", {})
        timeseries_data = algorithms_data.get("time_series", {})

        return cls(
            cpu=CPUConfig(
                collection=CPUCollectionConfig(**collection_data),
                detection=DetectionAlgorithmsConfig(
                    static=StaticDetectionConfig(**static_data),
                    dynamic_baseline=DynamicBaselineConfig(**dynamic_data),
                    time_series=TimeSeriesDetectionConfig(**timeseries_data),
                ),
                storage=StorageConfig(**storage_data),
                alerting=AlertingConfig(**alerting_data),
                output=OutputConfig(**output_data),
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
