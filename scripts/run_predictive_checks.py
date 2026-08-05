from ai.predictive_maintenance import compute_health_score, needs_maintenance, SimpleMaintenanceScheduler


def run_checks():
    assert compute_health_score([]) == 0.0

    readings = [0.9, 0.8, 0.7]
    score = compute_health_score(readings)
    assert 0.6 < score <= 0.9

    assert needs_maintenance(0.2) is True
    assert needs_maintenance(0.6) is False

    scheduler = SimpleMaintenanceScheduler()
    scores = {"unitA": 0.9, "unitB": 0.3, "unitC": 0.5}
    tasks = scheduler.prioritize(scores)
    assert tasks[0]["unit_id"] == "unitB"
    assert tasks[-1]["unit_id"] == "unitA"

    # exercise scheduling API
    schedule = scheduler.schedule_maintenance(scores, max_days=7)
    assert any(t["recommended_action"] in ("Monitor", "Schedule maintenance", "Immediate inspection") for t in schedule)
    print("Scheduler checks passed")

    print("All predictive maintenance checks passed")


if __name__ == "__main__":
    run_checks()
