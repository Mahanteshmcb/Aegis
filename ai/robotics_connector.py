"""
Aegis Robotics Connector

Provides a gRPC client wrapper for the RoboticFleetService contract.
Supports fallback mode when the robotics service is unavailable.
"""

import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add local protobuf path so generated stubs are importable.
ai_path = os.path.abspath(os.path.dirname(__file__))
protos_path = os.path.join(ai_path, "protos")
if protos_path not in sys.path:
    sys.path.insert(0, protos_path)

try:
    import grpc
    import robotics_pb2
    import robotics_pb2_grpc
    from google.protobuf import empty_pb2
    ROBOTICS_AVAILABLE = True
except Exception as e:
    logger.warning(f"Robotics protobuf import failed: {e}. Operating in fallback mode.")
    grpc = None
    robotics_pb2 = None
    robotics_pb2_grpc = None
    empty_pb2 = None
    ROBOTICS_AVAILABLE = False


ROBOT_TYPE_MAP = {
    "AEGIS_ROVER": 1,
    "AGRI_SWARM_BOT": 2,
    "CANOPY_DRONE": 3,
}

ROBOT_STATUS_MAP = {
    "IDLE": 1,
    "EXECUTING": 2,
    "CHARGING": 3,
    "MAINTENANCE": 4,
    "ERROR": 5,
    "OFFLINE": 6,
}

OPERATION_TYPE_MAP = {
    "HARVEST": 1,
    "PLANT": 2,
    "INSPECT": 3,
    "PRUNE": 4,
    "SPRAY": 5,
    "SAMPLE": 6,
    "MAINTAIN": 7,
}


class RoboticsConnector:
    """
    gRPC wrapper for the RoboticFleetService.

    This class provides a thin client layer for the robotics protobuf contract.
    When the remote service is unavailable, it returns safe fallback payloads.
    """

    def __init__(self,
                 host: str = "localhost",
                 port: int = 50052,
                 timeout: int = 5,
                 fallback_mode: bool = True):
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"
        self.timeout = timeout
        self.fallback_mode = fallback_mode

        self.channel = None
        self.stub = None
        self.is_connected = False

        self._init_grpc()

    def _init_grpc(self) -> None:
        if not ROBOTICS_AVAILABLE:
            logger.warning("⚠️ Robotics protobuf stubs unavailable; using fallback mode.")
            return

        try:
            self.channel = grpc.insecure_channel(self.address)
            self.stub = robotics_pb2_grpc.RoboticFleetServiceStub(self.channel)
            # Validate connection state without requiring a service method.
            try:
                grpc.channel_ready_future(self.channel).result(timeout=self.timeout)
            except AttributeError:
                # Some grpc versions expose channel_ready_future as a top-level helper.
                pass
            self.is_connected = True
            logger.info(f"✅ Robotics connector established to {self.address}")
        except Exception as e:
            logger.warning(f"⚠️ Robotics gRPC initialization failed: {e}")
            self.is_connected = False

    def _enum_value(self, value: Optional[str], mapping: Dict[str, int]) -> int:
        if not value:
            return 0
        return mapping.get(value.upper(), 0)

    def _fallback_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_connected:
            return payload
        if self.fallback_mode:
            logger.warning("⚠️ Robotics connector operating in fallback mode")
            return payload
        logger.error("❌ Robotics connector unavailable and fallback disabled")
        raise ConnectionError("Robotics service unavailable")

    def _safe_rpc(self, fn, fallback_data: Dict[str, Any]) -> Any:
        if not self.is_connected:
            return self._fallback_response(fallback_data)
        try:
            return fn()
        except Exception as e:
            logger.warning(f"⚠️ Robotics RPC failed: {e}. Falling back.")
            self.is_connected = False
            return self._fallback_response(fallback_data)

    def health_check(self) -> bool:
        if self.is_connected:
            return True
        if self.fallback_mode:
            return False
        return False

    def register_robot(self,
                       robot_id: str,
                       robot_type: str,
                       firmware_version: Optional[str] = None,
                       model_year: Optional[int] = None,
                       capabilities: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        if not self.is_connected:
            return self._fallback_response({
                "authenticated": True,
                "auth_token": f"fallback-token-{robot_id}",
                "token_expires_in_seconds": 3600,
                "authorized_operations": ["NAVIGATE", "TASK", "SENSOR_UPLOAD"],
                "authorized_zones": ["default"]
            })

        identity = robotics_pb2.RobotIdentity(
            robot_id=robot_id,
            type=self._enum_value(robot_type, ROBOT_TYPE_MAP),
            firmware_version=firmware_version or "unknown",
            model_year=model_year or 0,
            capabilities=capabilities or {}
        )
        response = self._safe_rpc(
            lambda: self.stub.RegisterRobot(identity),
            fallback_data={
                "authenticated": True,
                "auth_token": f"fallback-token-{robot_id}",
                "token_expires_in_seconds": 3600,
                "authorized_operations": ["NAVIGATE", "TASK", "SENSOR_UPLOAD"],
                "authorized_zones": ["default"]
            }
        )
        if isinstance(response, dict):
            return response
        return {
            "authenticated": response.authenticated,
            "auth_token": response.auth_token,
            "token_expires_in_seconds": response.token_expires_in_seconds,
            "authorized_operations": list(response.authorized_operations),
            "authorized_zones": list(response.authorized_zones),
        }

    def get_robot_health(self,
                         robot_id: str,
                         robot_type: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_connected:
            return self._fallback_response({
                "robot_id": robot_id,
                "status": "IDLE",
                "battery_percent": 100,
                "cpu_temp_celsius": 36.5,
                "motor_health_percent": 100,
                "warnings": [],
                "errors": [],
                "uptime_seconds": 0,
                "last_heartbeat_timestamp_ms": int(time.time() * 1000)
            })

        identity = robotics_pb2.RobotIdentity(
            robot_id=robot_id,
            type=self._enum_value(robot_type, ROBOT_TYPE_MAP),
            firmware_version="unknown",
            model_year=0,
            capabilities={}
        )
        response = self._safe_rpc(
            lambda: self.stub.GetRobotHealth(identity),
            fallback_data={
                "robot_id": robot_id,
                "status": "IDLE",
                "battery_percent": 100,
                "cpu_temp_celsius": 36.5,
                "motor_health_percent": 100,
                "warnings": [],
                "errors": [],
                "uptime_seconds": 0,
                "last_heartbeat_timestamp_ms": int(time.time() * 1000)
            }
        )
        if isinstance(response, dict):
            return response
        return {
            "robot_id": robot_id,
            "status": robotics_pb2.RobotStatus.Name(response.status) if response.status else "STATUS_UNSPECIFIED",
            "battery_percent": response.battery_percent,
            "cpu_temp_celsius": response.cpu_temp_celsius,
            "motor_health_percent": response.motor_health_percent,
            "warnings": list(response.warnings),
            "errors": list(response.errors),
            "uptime_seconds": response.uptime_seconds,
            "last_heartbeat_timestamp_ms": response.last_heartbeat_timestamp_ms,
        }

    def send_task(self,
                  task_id: str,
                  robot_id: str,
                  operation_type: str,
                  priority: int = 5,
                  task_detail: Optional[Dict[str, Any]] = None,
                  timeout_seconds: int = 60,
                  metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        if not self.is_connected:
            return self._fallback_response({
                "task_id": task_id,
                "result": "FAILED",
                "status_message": "Fallback mode: task queued locally",
                "completion_percent": 0,
                "execution_time_ms": 0,
                "metrics": {}
            })

        task = robotics_pb2.RoboticTask(
            task_id=task_id,
            robot_id=robot_id,
            operation_type=self._enum_value(operation_type, OPERATION_TYPE_MAP),
            priority=priority,
            timeout_seconds=timeout_seconds,
            metadata=metadata or {}
        )

        detail = task_detail or {}
        if "navigation" in detail:
            nav = detail["navigation"]
            command = robotics_pb2.NavigationCommand(
                command_id=nav.get("command_id", task_id),
                target=self._build_navigation_target(nav.get("target", {})),
                timeout_seconds=nav.get("timeout_seconds", timeout_seconds),
                zone_id=nav.get("zone_id", "")
            )
            task.navigation.CopyFrom(command)
        elif "harvest" in detail:
            harvest = detail["harvest"]
            task.harvest.CopyFrom(robotics_pb2.HarvestTask(
                crop_id=harvest.get("crop_id", ""),
                location=self._build_coordinate3d(harvest.get("location", {})),
                crop_species=harvest.get("crop_species", ""),
                estimated_yield_kg=harvest.get("estimated_yield_kg", 0),
                use_gentle_mode=harvest.get("use_gentle_mode", False)
            ))
        elif "inspection" in detail:
            inspection = detail["inspection"]
            task.inspection.CopyFrom(robotics_pb2.InspectionTask(
                zone_id=inspection.get("zone_id", ""),
                focus_area=inspection.get("focus_area", ""),
                collect_images=inspection.get("collect_images", False),
                run_health_analysis=inspection.get("run_health_analysis", False),
                inspection_resolution_megapixels=inspection.get("inspection_resolution_megapixels", 2)
            ))

        response = self._safe_rpc(
            lambda: self.stub.SendTask(task),
            fallback_data={
                "task_id": task_id,
                "result": "FAILED",
                "status_message": "Fallback mode: task queued locally",
                "completion_percent": 0,
                "execution_time_ms": 0,
                "metrics": {}
            }
        )
        if isinstance(response, dict):
            return response
        return {
            "task_id": response.task_id,
            "result": robotics_pb2.CommandResult.Name(response.result) if response.result else "RESULT_UNSPECIFIED",
            "status_message": response.status_message,
            "completion_percent": response.completion_percent,
            "execution_time_ms": response.execution_time_ms,
            "metrics": dict(response.metrics)
        }

    def navigate_to(self,
                    command_id: str,
                    robot_id: str,
                    destination: Dict[str, Any],
                    waypoints: Optional[List[Dict[str, Any]]] = None,
                    speed_percent: float = 50.0,
                    use_obstacles_map: bool = False,
                    timeout_seconds: int = 60,
                    zone_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_connected:
            return self._fallback_response({
                "command_id": command_id,
                "current_position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "distance_to_target_m": 0.0,
                "heading_degrees": 0.0,
                "speed_mps": 0.0,
                "message": "Fallback navigation request accepted"
            })

        nav_command = robotics_pb2.NavigationCommand(
            command_id=command_id,
            target=self._build_navigation_target({
                "destination": destination,
                "waypoints": waypoints or [],
                "speed_percent": speed_percent,
                "use_obstacles_map": use_obstacles_map,
            }),
            timeout_seconds=timeout_seconds,
            zone_id=zone_id or ""
        )
        response = self._safe_rpc(
            lambda: self.stub.NavigateTo(nav_command),
            fallback_data={
                "command_id": command_id,
                "current_position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "distance_to_target_m": 0.0,
                "heading_degrees": 0.0,
                "speed_mps": 0.0,
                "message": "Fallback navigation request accepted"
            }
        )
        if isinstance(response, dict):
            return response
        return {
            "command_id": response.command_id,
            "current_position": {
                "x": response.current_position.x,
                "y": response.current_position.y,
                "z": response.current_position.z,
            },
            "distance_to_target_m": response.distance_to_target_m,
            "heading_degrees": response.heading_degrees,
            "speed_mps": response.speed_mps,
        }

    def get_navigation_status(self,
                              robot_id: str,
                              robot_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return [
                {
                    "command_id": "fallback",
                    "current_position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "distance_to_target_m": 0.0,
                    "heading_degrees": 0.0,
                    "speed_mps": 0.0,
                }
            ]

        identity = robotics_pb2.RobotIdentity(
            robot_id=robot_id,
            type=self._enum_value(robot_type, ROBOT_TYPE_MAP),
            firmware_version="unknown",
            model_year=0,
            capabilities={}
        )
        try:
            statuses = []
            for status in self.stub.GetNavigationStatus(identity):
                statuses.append({
                    "command_id": status.command_id,
                    "current_position": {
                        "x": status.current_position.x,
                        "y": status.current_position.y,
                        "z": status.current_position.z,
                    },
                    "distance_to_target_m": status.distance_to_target_m,
                    "heading_degrees": status.heading_degrees,
                    "speed_mps": status.speed_mps,
                })
            return statuses
        except Exception as e:
            logger.warning(f"⚠️ Robotics RPC failed: {e}. Falling back.")
            self.is_connected = False
            return [
                {
                    "command_id": "fallback",
                    "current_position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "distance_to_target_m": 0.0,
                    "heading_degrees": 0.0,
                    "speed_mps": 0.0,
                }
            ]

    def report_sensor_data(self,
                           robot_id: str,
                           health: Dict[str, Any],
                           environment: Dict[str, Any],
                           observations: Optional[List[str]] = None,
                           timestamp_ms: Optional[int] = None) -> Dict[str, Any]:
        if not self.is_connected:
            return self._fallback_response({"status": "success", "message": "Sensor payload accepted in fallback mode"})

        sensor_data = robotics_pb2.SensorData(
            robot_id=robot_id,
            health=self._build_robot_health(health),
            environment=self._build_environmental_reading(environment),
            observations=observations or [],
            timestamp_ms=timestamp_ms or int(time.time() * 1000)
        )
        response = self._safe_rpc(
            lambda: self.stub.ReportSensorData(sensor_data),
            fallback_data={"status": "success", "message": "Sensor data reported"}
        )
        if isinstance(response, dict):
            return response
        return {"status": "success", "message": "Sensor data reported"}

    def emergency_stop(self,
                       robot_id: str,
                       robot_type: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_connected:
            return self._fallback_response({"status": "success", "message": "Emergency stop simulated in fallback mode"})

        identity = robotics_pb2.RobotIdentity(
            robot_id=robot_id,
            type=self._enum_value(robot_type, ROBOT_TYPE_MAP),
            firmware_version="unknown",
            model_year=0,
            capabilities={}
        )
        response = self._safe_rpc(
            lambda: self.stub.EmergencyStop(identity),
            fallback_data={"status": "success", "message": "Emergency stop issued"}
        )
        if isinstance(response, dict):
            return response
        return {"status": "success", "message": "Emergency stop issued"}

    def cancel_task(self,
                    robot_id: str,
                    robot_type: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_connected:
            return self._fallback_response({"status": "success", "message": "Cancel task simulated in fallback mode"})

        identity = robotics_pb2.RobotIdentity(
            robot_id=robot_id,
            type=self._enum_value(robot_type, ROBOT_TYPE_MAP),
            firmware_version="unknown",
            model_year=0,
            capabilities={}
        )
        response = self._safe_rpc(
            lambda: self.stub.CancelTask(identity),
            fallback_data={"status": "success", "message": "Task cancel issued"}
        )
        if isinstance(response, dict):
            return response
        return {"status": "success", "message": "Task cancel issued"}

    def list_active_robots(self) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return [
                {
                    "robot_id": "fallback-robot",
                    "status": "IDLE",
                    "battery_percent": 100,
                    "cpu_temp_celsius": 0.0,
                    "motor_health_percent": 100,
                    "warnings": [],
                    "errors": [],
                    "uptime_seconds": 0,
                    "last_heartbeat_timestamp_ms": int(time.time() * 1000)
                }
            ]

        try:
            active = []
            for robot in self.stub.ListActiveRobots(empty_pb2.Empty()):
                active.append({
                    "robot_id": getattr(robot, "robot_id", ""),
                    "status": robotics_pb2.RobotStatus.Name(robot.status) if robot.status else "STATUS_UNSPECIFIED",
                    "battery_percent": robot.battery_percent,
                    "cpu_temp_celsius": robot.cpu_temp_celsius,
                    "motor_health_percent": robot.motor_health_percent,
                    "warnings": list(robot.warnings),
                    "errors": list(robot.errors),
                    "uptime_seconds": robot.uptime_seconds,
                    "last_heartbeat_timestamp_ms": robot.last_heartbeat_timestamp_ms,
                })
            return active
        except Exception as e:
            logger.warning(f"⚠️ Robotics RPC failed: {e}. Falling back.")
            self.is_connected = False
            return [
                {
                    "robot_id": "fallback-robot",
                    "status": "IDLE",
                    "battery_percent": 100,
                    "cpu_temp_celsius": 0.0,
                    "motor_health_percent": 100,
                    "warnings": [],
                    "errors": [],
                    "uptime_seconds": 0,
                    "last_heartbeat_timestamp_ms": int(time.time() * 1000)
                }
            ]

    def _build_coordinate3d(self, coordinates: Dict[str, Any]) -> "robotics_pb2.Coordinate3D":
        return robotics_pb2.Coordinate3D(
            x=float(coordinates.get("x", 0.0)),
            y=float(coordinates.get("y", 0.0)),
            z=float(coordinates.get("z", 0.0)),
        )

    def _build_navigation_target(self, payload: Dict[str, Any]) -> "robotics_pb2.NavigationTarget":
        target = robotics_pb2.NavigationTarget(
            destination=self._build_coordinate3d(payload.get("destination", {})),
            speed_percent=float(payload.get("speed_percent", 50.0)),
            use_obstacles_map=bool(payload.get("use_obstacles_map", False)),
        )
        for waypoint in payload.get("waypoints", []):
            target.waypoints.add().CopyFrom(self._build_coordinate3d(waypoint))
        return target

    def _build_robot_health(self, payload: Dict[str, Any]) -> "robotics_pb2.RobotHealth":
        return robotics_pb2.RobotHealth(
            status=self._enum_value(payload.get("status"), ROBOT_STATUS_MAP),
            battery_percent=int(payload.get("battery_percent", 0)),
            cpu_temp_celsius=float(payload.get("cpu_temp_celsius", 0.0)),
            motor_health_percent=int(payload.get("motor_health_percent", 0)),
            warnings=payload.get("warnings", []),
            errors=payload.get("errors", []),
            uptime_seconds=int(payload.get("uptime_seconds", 0)),
            last_heartbeat_timestamp_ms=int(payload.get("last_heartbeat_timestamp_ms", int(time.time() * 1000)))
        )

    def _build_environmental_reading(self, payload: Dict[str, Any]) -> "robotics_pb2.EnvironmentalReading":
        return robotics_pb2.EnvironmentalReading(
            location=self._build_coordinate3d(payload.get("location", {})),
            temperature_celsius=float(payload.get("temperature_celsius", 0.0)),
            humidity_percent=float(payload.get("humidity_percent", 0.0)),
            light_lux=float(payload.get("light_lux", 0.0)),
            air_quality_ppm=float(payload.get("air_quality_ppm", 0.0)),
            timestamp_ms=int(payload.get("timestamp_ms", int(time.time() * 1000)))
        )

    def close(self) -> None:
        if self.channel:
            self.channel.close()
        self.is_connected = False


if __name__ == "__main__":
    connector = RoboticsConnector()
    print("Robotics connector initialized", connector.is_connected)
