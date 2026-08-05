"""Predictive maintenance helpers (Day 52 skeleton).

This module provides a simple heuristic-based predictive maintenance
interface and a tiny scikit-learn-compatible wrapper for future model
integration.
"""
from typing import Dict, Any, List
import numpy as np
from dataclasses import dataclass
import datetime


def compute_health_score(sensor_readings: List[float]) -> float:
    """Compute a simple health score from recent sensor readings.

    Args:
        sensor_readings: list of recent normalized health metrics (0..1)

    Returns:
        health_score: float in 0..1 where lower means worse health
    """
    if not sensor_readings:
        return 0.0
    arr = np.array(sensor_readings, dtype=float)
    # simple exponentially weighted moving average
    weights = np.exp(-0.5 * np.arange(len(arr))[::-1])
    score = float(np.sum(arr * weights) / np.sum(weights))
    return max(0.0, min(1.0, score))


def needs_maintenance(health_score: float, threshold: float = 0.4) -> bool:
    """Decide whether the unit needs maintenance.

    Use a conservative threshold by default; this can be replaced with a
    learned model later.
    """
    return health_score < threshold


class SimpleMaintenanceScheduler:
    """Create maintenance schedules from health scores.

    The scheduler accepts a mapping of `unit_id -> health_score` and
    returns prioritized maintenance tasks.
    """

    def prioritize(self, scores: Dict[str, float]) -> List[Dict[str, Any]]:
        tasks = []
        for uid, score in scores.items():
            priority = int((1.0 - score) * 100)
            tasks.append({"unit_id": uid, "health_score": score, "priority": priority})
        # sort by priority descending (higher priority first)
        tasks.sort(key=lambda t: t["priority"], reverse=True)
        return tasks

    def schedule_maintenance(self, scores: Dict[str, float], max_days: int = 14) -> List[Dict[str, Any]]:
        """Create a maintenance schedule with ETA and recommended action.

        Args:
            scores: mapping of unit_id -> health_score (0..1)
            max_days: maximum days until maintenance for a perfectly healthy unit

        Returns:
            List of task dicts with `unit_id`, `health_score`, `priority`, `eta_days`, `recommended_action`.
        """
        tasks = []
        for uid, score in scores.items():
            priority = int((1.0 - score) * 100)
            # higher health -> longer time before maintenance; lower health -> sooner
            eta_days = max(1, int(score * max_days))
            if score < 0.2:
                action = "Immediate inspection"
            elif score < 0.5:
                action = "Schedule maintenance"
            else:
                action = "Monitor"

            tasks.append({
                "unit_id": uid,
                "health_score": score,
                "priority": priority,
                "eta_days": eta_days,
                "recommended_action": action,
            })

        tasks.sort(key=lambda t: t["priority"], reverse=True)
        return tasks


__all__ = ["compute_health_score", "needs_maintenance", "SimpleMaintenanceScheduler"]
