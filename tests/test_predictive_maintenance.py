import math
from ai.predictive_maintenance import compute_health_score, needs_maintenance, SimpleMaintenanceScheduler


def test_compute_health_score_empty():
    assert compute_health_score([]) == 0.0


def test_compute_health_score_values():
    readings = [0.9, 0.8, 0.7]
    score = compute_health_score(readings)
    assert 0.6 < score <= 0.9


def test_needs_maintenance():
    assert needs_maintenance(0.2) is True
    assert needs_maintenance(0.6) is False


def test_scheduler_prioritize():
    scheduler = SimpleMaintenanceScheduler()
    scores = {"unitA": 0.9, "unitB": 0.3, "unitC": 0.5}
    tasks = scheduler.prioritize(scores)
    assert tasks[0]["unit_id"] == "unitB"
    assert tasks[-1]["unit_id"] == "unitA"
