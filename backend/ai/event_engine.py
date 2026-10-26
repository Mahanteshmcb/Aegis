from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import networkx as nx  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class ThresholdRule:
    """A threshold rule that evaluates a sensor metric against bounds.

    When violated, it can trigger:
      - An alert (SystemAlert)
      - A robotic dispatch (ScheduledRoboticTask)
    """
    rule_id: str
    name: str
    sensor_type: str  # e.g. "soil_moisture", "temperature"
    metric: str  # e.g. "moisture", "temp_c"
    comparator: str  # "lt" (less-than) or "gt" (greater-than)
    threshold: float
    zone_id: Optional[str] = None  # None = applies across all zones
    severity: str = "medium"  # "low" | "medium" | "high"
    cooldown_seconds: int = 300  # debounce to avoid alert storms
    enabled: bool = True

    # Derived during engine init
    last_triggered: float = field(default=0.0, repr=False)
class EventEngine:
    """Evaluates ThresholdRule instances against live or simulated sensor data.

    Persists alerts to SQLite (SystemAlert) and creates dispatch tasks
    (ScheduledRoboticTask) when rules are violated.
    """

    def __init__(self, rules: List[ThresholdRule] = None, graph: Optional[nx.Graph] = None):
        self.rules = rules or []
        self.graph = graph  # NetworkX spatial graph (EstateGraph output)
        self._rule_index: Dict[str, ThresholdRule] = {
            r.rule_id: r for r in self.rules
        }
        # Zone -> list of rules that apply in that zone
        self._zone_rules: Dict[str, List[ThresholdRule]] = {}
        if self.graph is not None:
            for rule in self.rules:
                if rule.zone_id:
                    self._zone_rules.setdefault(rule.zone_id, []).append(rule)
                else:
                    # zone-less rule applies everywhere
                    for zone_node, zone_data in self.graph.nodes(data=True):
                        if zone_data.get("node_type") == "zone":
                            self._zone_rules.setdefault(
                                zone_data.get("zone_id", ""), []
                            ).append(rule)

    def evaluate_sensor_reading(
        self,
        sensor_type: str,
        metric_value: float,
        zone_id: str,
        timestamp: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Evaluate all applicable rules for a sensor reading.

        Returns a list of triggered events, each a dict with keys:
          - "rule_id"
          - "rule_name"
          - "event_type": "alert" | "dispatch"
          - "severity"
          - "message"
        """
        timestamp = timestamp or time.time()
        triggered: List[Dict[str, Any]] = []

        # Gather applicable rules for this zone
        applicable = self._zone_rules.get(zone_id, [])
        applicable.extend(self._zone_rules.get("", []))  # zone-less rules

        for rule in applicable:
            if not rule.enabled:
                continue
            # Cooldown check
            if timestamp - rule.last_triggered < rule.cooldown_seconds:
                continue

            # Evaluate comparator
            violated = False
            if rule.comparator == "lt":
                violated = metric_value < rule.threshold
            elif rule.comparator == "gt":
                violated = metric_value > rule.threshold

            if violated:
                rule.last_triggered = timestamp
                event_type = "alert" if rule.severity in ("low", "medium") else "dispatch"
                # For severe violations, generate a dispatch task
                if rule.severity == "high":
                    event_type = "dispatch"

                event = {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "event_type": event_type,
                    "severity": rule.severity,
                    "message": f"[{rule.sensor_type}] {rule.metric} {rule.comparator} {rule.threshold} (value={metric_value:.2f}) in zone {zone_id}",
                    "metric_value": metric_value,
                    "threshold": rule.threshold,
                    "timestamp": timestamp,
                }
                triggered.append(event)

        return triggered

    def suggest_dispatch(
        self,
        sensor_type: str,
        metric_value: float,
        zone_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Convenience: returns the highest-severity dispatch suggestion,
        or None if no dispatch warranted.
        """
        applicable = self._zone_rules.get(zone_id, [])
        applicable.extend(self._zone_rules.get("", []))
        dispatch_rules = [
            r for r in applicable
            if r.enabled and r.severity == "high"
        ]
        if not dispatch_rules:
            return None
        # Pick the first high-severity rule (should be unique per sensor type)
        r = dispatch_rules[0]
        return {
            "rule_id": r.rule_id,
            "name": r.name,
            "metric": r.metric,
            "threshold": r.threshold,
            "value": metric_value,
            "zone_id": zone_id,
        }


# Global engine instance (importable; initialized during app startup)
engine: Optional[EventEngine] = None


def init_engine(rules: List[ThresholdRule], graph: nx.Graph) -> EventEngine:
    global engine
    engine = EventEngine(rules=rules, graph=graph)
    return engine