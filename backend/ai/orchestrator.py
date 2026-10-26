from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.ai.event_engine import EventEngine, init_engine, engine as global_engine, ThresholdRule
from backend.estate_config import load_estate_config, build_graph, load_and_persist

logger = logging.getLogger(__name__)


# ── Engine lifecycle ──────────────────────────────────────────────


def start_engine(rules: List[ThresholdRule], config_path: str = "estate_config.json"):
    """Initialize and start the event engine with rules and spatial graph.

    Call during FastAPI app startup (e.g. in main.py lifespan).
    """
    try:
        cfg = load_estate_config(config_path)
        graph = build_graph(cfg)
    except FileNotFoundError:
        logger.warning("Estate config not found at %s; engine starting without graph", config_path)
        graph = None

    init_engine(rules=rules, graph=graph)
    logger.info("Event engine initialized: %s rules, graph=%s", len(rules), graph is not None)
    return global_engine


def evaluate_reading(sensor_type: str, metric_value: float, zone_id: str) -> List[Dict[str, Any]]:
    """Convenience: evaluate a sensor reading against the active rule set.

    Intended to be called from the sensors realtime handler.
    """
    if global_engine is None:
        return []
    return global_engine.evaluate_sensor_reading(sensor_type, metric_value, zone_id)


def suggest_dispatch(sensor_type: str, metric_value: float, zone_id: str) -> Optional[Dict[str, Any]]:
    """Convenience: get a dispatch suggestion for a sensor reading."""
    if global_engine is None:
        return None
    return global_engine.suggest_dispatch(sensor_type, metric_value, zone_id)


# ── Pre-seeded default rules for a typical agricultural estate ─────


DEFAULT_RULES = [
    ThresholdRule(
        rule_id="moisture_low",
        name="Low Soil Moisture Alert",
        sensor_type="soil_moisture",
        metric="moisture",
        comparator="lt",
        threshold=30.0,  # %; below 30% is critical
        severity="high",
        cooldown_seconds=300,
        enabled=True,
    ),
    ThresholdRule(
        rule_id="temp_high",
        name="High Temperature Alert",
        sensor_type="temperature",
        metric="temp_c",
        comparator="gt",
        threshold=35.0,  # °C; above 35°C is critical
        severity="high",
        cooldown_seconds=300,
        enabled=True,
    ),
    ThresholdRule(
        rule_id="motion_detected",
        name="Intrusion Motion Detected",
        sensor_type="motion",
        metric="motion_count",
        comparator="gt",
        threshold=0,
        severity="high",
        cooldown_seconds=60,
        enabled=True,
    ),
]


# ── Exported for main.py lifespan ─────────────────────────────────

engine = start_engine(rules=DEFAULT_RULES)