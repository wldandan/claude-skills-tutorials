"""Alert manager."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
from pathlib import Path
from aiops.alerting.models import AlertRule, Alert, AlertStatus


class AlertManager:
    """Manage alert rules and alerts."""

    def __init__(self, storage_path: str = "/tmp/aiops/alerts"):
        """Initialize alert manager.

        Args:
            storage_path: Path to store alert data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.rules_file = self.storage_path / "rules.json"
        self.alerts_file = self.storage_path / "alerts.json"

    def create_rule(self, rule: AlertRule) -> None:
        """Create alert rule.

        Args:
            rule: AlertRule to create
        """
        rules = self.list_rules()

        # Check if rule already exists
        if any(r['name'] == rule.name for r in rules):
            raise ValueError(f"Rule '{rule.name}' already exists")

        # Set timestamps
        rule.created_at = datetime.now()
        rule.updated_at = datetime.now()

        # Add rule
        rules.append(rule.to_dict())

        # Save
        self._save_rules(rules)

    def list_rules(self) -> List[Dict[str, Any]]:
        """List all alert rules.

        Returns:
            List of alert rules
        """
        if not self.rules_file.exists():
            return []

        with open(self.rules_file, 'r') as f:
            return json.load(f)

    def get_rule(self, name: str) -> Optional[Dict[str, Any]]:
        """Get alert rule by name.

        Args:
            name: Rule name

        Returns:
            Rule dict or None
        """
        rules = self.list_rules()
        for rule in rules:
            if rule['name'] == name:
                return rule
        return None

    def delete_rule(self, name: str) -> None:
        """Delete alert rule.

        Args:
            name: Rule name
        """
        rules = self.list_rules()
        rules = [r for r in rules if r['name'] != name]
        self._save_rules(rules)

    def enable_rule(self, name: str) -> None:
        """Enable alert rule.

        Args:
            name: Rule name
        """
        self._update_rule_status(name, True)

    def disable_rule(self, name: str) -> None:
        """Disable alert rule.

        Args:
            name: Rule name
        """
        self._update_rule_status(name, False)

    def _update_rule_status(self, name: str, enabled: bool) -> None:
        """Update rule enabled status.

        Args:
            name: Rule name
            enabled: Enabled status
        """
        rules = self.list_rules()
        for rule in rules:
            if rule['name'] == name:
                rule['enabled'] = enabled
                rule['updated_at'] = datetime.now().isoformat()
                break
        self._save_rules(rules)

    def create_alert(self, alert: Alert) -> None:
        """Create alert.

        Args:
            alert: Alert to create
        """
        alerts = self.list_alerts()
        alerts.append(alert.to_dict())
        self._save_alerts(alerts)

    def list_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List alerts.

        Args:
            status: Filter by status
            severity: Filter by severity

        Returns:
            List of alerts
        """
        if not self.alerts_file.exists():
            return []

        with open(self.alerts_file, 'r') as f:
            alerts = json.load(f)

        # Filter
        if status:
            alerts = [a for a in alerts if a['status'] == status]
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]

        return alerts

    def acknowledge_alert(self, rule_name: str, user: str) -> None:
        """Acknowledge alert.

        Args:
            rule_name: Rule name
            user: User who acknowledged
        """
        alerts = self.list_alerts()
        for alert in alerts:
            if alert['rule_name'] == rule_name and alert['status'] == AlertStatus.FIRING.value:
                alert['status'] = AlertStatus.ACKNOWLEDGED.value
                alert['acknowledged_at'] = datetime.now().isoformat()
                alert['acknowledged_by'] = user
                break
        self._save_alerts(alerts)

    def resolve_alert(self, rule_name: str) -> None:
        """Resolve alert.

        Args:
            rule_name: Rule name
        """
        alerts = self.list_alerts()
        for alert in alerts:
            if alert['rule_name'] == rule_name and alert['status'] in [
                AlertStatus.FIRING.value,
                AlertStatus.ACKNOWLEDGED.value
            ]:
                alert['status'] = AlertStatus.RESOLVED.value
                alert['ended_at'] = datetime.now().isoformat()
                break
        self._save_alerts(alerts)

    def _save_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Save rules to file.

        Args:
            rules: List of rules
        """
        with open(self.rules_file, 'w') as f:
            json.dump(rules, f, indent=2)

    def _save_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """Save alerts to file.

        Args:
            alerts: List of alerts
        """
        with open(self.alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)
