"""Local robotics gRPC service used by the software-first Phase 2 demo."""
from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import grpc

PROTO_DIR = os.path.join(os.path.dirname(__file__), "protos")
if PROTO_DIR not in sys.path:
    sys.path.insert(0, PROTO_DIR)

import robotics_pb2
import robotics_pb2_grpc
from google.protobuf import empty_pb2


class DemoRoboticFleetService(robotics_pb2_grpc.RoboticFleetServiceServicer):
    """Deterministic fleet service that exercises the production protobuf contract."""

    def __init__(self):
        self.robots: dict[str, robotics_pb2.RobotIdentity] = {}
        self.health: dict[str, robotics_pb2.RobotHealth] = {}
        self.positions: dict[str, robotics_pb2.Coordinate3D] = {}
        self.tasks: dict[str, robotics_pb2.TaskResult] = {}

    def RegisterRobot(self, request, context):
        self.robots[request.robot_id] = request
        self.health.setdefault(
            request.robot_id,
            robotics_pb2.RobotHealth(
                status=robotics_pb2.IDLE,
                battery_percent=86,
                cpu_temp_celsius=42.0,
                motor_health_percent=98,
                uptime_seconds=1,
                last_heartbeat_timestamp_ms=int(time.time() * 1000),
            ),
        )
        self.positions.setdefault(request.robot_id, robotics_pb2.Coordinate3D())
        return robotics_pb2.RobotAuthResponse(
            authenticated=True,
            auth_token=f"demo-token-{request.robot_id}",
            token_expires_in_seconds=3600,
            authorized_operations=["NAVIGATE", "TASK", "SENSOR_UPLOAD"],
            authorized_zones=["Main Lab Zone", "Field A", "Power Shed"],
        )

    def GetRobotHealth(self, request, context):
        health = self.health.get(request.robot_id)
        if health is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "Robot is not registered")
        health.last_heartbeat_timestamp_ms = int(time.time() * 1000)
        return health

    def SendTask(self, request, context):
        if request.robot_id not in self.robots:
            context.abort(grpc.StatusCode.NOT_FOUND, "Robot is not registered")
        result = robotics_pb2.TaskResult(
            task_id=request.task_id,
            result=robotics_pb2.SUCCESS,
            status_message="Task accepted by the software-first fleet simulator",
            completion_percent=100,
            execution_time_ms=25,
            metrics={"mode": "simulated", "robot_id": request.robot_id},
        )
        self.tasks[request.task_id] = result
        self.health[request.robot_id].status = robotics_pb2.IDLE
        return result

    def NavigateTo(self, request, context):
        robot_id = next(iter(self.robots), None)
        if robot_id is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "No robot is registered")
        destination = request.target.destination if request.HasField("target") else robotics_pb2.Coordinate3D()
        self.positions[robot_id] = destination
        return robotics_pb2.NavigationStatus(
            command_id=request.command_id,
            current_position=destination,
            distance_to_target_m=0.0,
            heading_degrees=0.0,
            speed_mps=0.0,
        )

    def GetNavigationStatus(self, request, context):
        position = self.positions.get(request.robot_id, robotics_pb2.Coordinate3D())
        yield robotics_pb2.NavigationStatus(
            command_id="latest",
            current_position=position,
            distance_to_target_m=0.0,
            heading_degrees=0.0,
            speed_mps=0.0,
        )

    def ReportSensorData(self, request, context):
        if request.robot_id in self.health and request.HasField("health"):
            self.health[request.robot_id].CopyFrom(request.health)
        return empty_pb2.Empty()

    def EmergencyStop(self, request, context):
        if request.robot_id in self.health:
            self.health[request.robot_id].status = robotics_pb2.OFFLINE
        return empty_pb2.Empty()

    def CancelTask(self, request, context):
        return empty_pb2.Empty()

    def ListActiveRobots(self, request, context):
        for robot_id in self.robots:
            yield self.health[robot_id]


def create_robotics_server(host: str = "127.0.0.1", port: int = 50052):
    """Create a synchronous gRPC server for local/demo and integration use."""
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    robotics_pb2_grpc.add_RoboticFleetServiceServicer_to_server(DemoRoboticFleetService(), server)
    server.add_insecure_port(f"{host}:{port}")
    return server
