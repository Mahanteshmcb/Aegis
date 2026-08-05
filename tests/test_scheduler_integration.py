from ai.predictive_maintenance import SimpleMaintenanceScheduler


def test_schedule_maintenance_contents():
    scheduler = SimpleMaintenanceScheduler()
    scores = {"A": 0.9, "B": 0.1, "C": 0.5}
    tasks = scheduler.schedule_maintenance(scores, max_days=10)

    # B should have highest priority (lowest health)
    assert tasks[0]["unit_id"] == "B"
    assert tasks[0]["recommended_action"] == "Immediate inspection"

    # A should be monitored and have larger eta_days
    a_task = next(t for t in tasks if t["unit_id"] == "A")
    assert a_task["recommended_action"] == "Monitor"
    assert a_task["eta_days"] >= 1
