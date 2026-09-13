"""
Aegis Robotics Task Scheduler

Provides priority-based task queueing, simple assignment, and conflict resolution
for the robotic fleet.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai.robotics_connector import RoboticsConnector


@dataclass
class RoboticTask:
    task_id: str
    operation_type: str
    robot_id: Optional[str] = None
    zone_id: Optional[str] = None
    priority: int = 5
    task_detail: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 60
    status: str = "pending"
    enqueue_time: datetime = field(default_factory=datetime.utcnow)
    conflict_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "operation_type": self.operation_type,
            "robot_id": self.robot_id,
            "zone_id": self.zone_id,
            "priority": self.priority,
            "status": self.status,
            "task_detail": self.task_detail,
            "metadata": self.metadata,
            "timeout_seconds": self.timeout_seconds,
            "enqueue_time": self.enqueue_time.isoformat(),
            "conflict_reason": self.conflict_reason,
        }


class TaskScheduler:
    """Simple task queue manager for robotic fleet scheduling."""

    def __init__(self, robotics_connector: RoboticsConnector):
        self.connector = robotics_connector
        self.queue: List[RoboticTask] = []
        self.assignments: Dict[str, str] = {}

    def enqueue_task(self, task: RoboticTask) -> None:
        task.status = "pending"
        task.conflict_reason = None
        self.queue.append(task)
        self.queue.sort(key=lambda t: (-t.priority, t.enqueue_time))

    def get_queue(self) -> List[RoboticTask]:
        return list(self.queue)

    def assign_pending_tasks(self) -> List[Dict[str, Any]]:
        active_robots = self.connector.list_active_robots()
        idle_robots = []
        for robot in active_robots:
            status = str(robot.get("status") or "").upper()
            if status in {"IDLE", "ACTIVE", "READY"}:
                robot_id = robot.get("robot_id") or robot.get("id")
                if robot_id:
                    idle_robots.append(robot_id)
        assigned_tasks: List[Dict[str, Any]] = []

        pending_tasks = [task for task in self.queue if task.status == "pending"]
        pending_tasks.sort(key=lambda t: (-t.priority, t.enqueue_time))

        # Detect simple conflicts: same zone + same operation.
        seen_operations: Dict[tuple, RoboticTask] = {}
        for task in pending_tasks:
            key = (task.zone_id, task.operation_type)
            if task.zone_id is not None and key in seen_operations:
                existing = seen_operations[key]
                lower, higher = (task, existing) if task.priority < existing.priority else (existing, task)
                lower.status = "conflicted"
                lower.conflict_reason = "Overlapping task in same zone with higher priority"
                if lower.task_id in self.assignments:
                    del self.assignments[lower.task_id]
                if higher is task:
                    seen_operations[key] = task
            else:
                seen_operations[key] = task

        for task in pending_tasks:
            if task.status != "pending":
                continue

            if task.robot_id:
                if task.robot_id not in idle_robots:
                    task.status = "conflicted"
                    task.conflict_reason = f"Assigned robot {task.robot_id} unavailable"
                    continue
                selected_robot = task.robot_id
                idle_robots.remove(selected_robot)
            elif idle_robots:
                selected_robot = self._select_robot_for_task(task, idle_robots)
                task.robot_id = selected_robot
                idle_robots.remove(selected_robot)
            else:
                task.status = "conflicted"
                task.conflict_reason = "No idle robots available"
                continue

            task.status = "assigned"
            self.assignments[task.task_id] = selected_robot

            response = self.connector.send_task(
                task_id=task.task_id,
                robot_id=selected_robot,
                operation_type=task.operation_type,
                priority=task.priority,
                task_detail=task.task_detail,
                timeout_seconds=task.timeout_seconds,
                metadata=task.metadata,
            )
            assigned_tasks.append({
                "task_id": task.task_id,
                "robot_id": selected_robot,
                "status": task.status,
                "response": response,
                "conflict_reason": task.conflict_reason,
            })

        return assigned_tasks

    def get_queue_status(self) -> Dict[str, Any]:
        queue = [task.to_dict() for task in self.queue]
        in_progress = [task.to_dict() for task in self.queue if task.status == "assigned"]
        conflicted = [task.to_dict() for task in self.queue if task.status == "conflicted"]
        return {
            "queue_length": len(queue),
            "assigned": len(in_progress),
            "conflicted": len(conflicted),
            "tasks": queue,
        }

    def _select_robot_for_task(self, task: RoboticTask, idle_robots: List[str]) -> str:
        if not idle_robots:
            raise ValueError("No idle robot available")
        # Simple round-robin / first-available selection. In the future, use capability matching.
        return idle_robots[0]
