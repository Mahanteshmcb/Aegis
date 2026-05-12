# Day 37: Integration testing for gRPC contracts
# Mock robotic clients and sensor simulators for comprehensive testing

import asyncio
import logging
import time
import random
from typing import Dict, List, Optional, Any
from concurrent import futures
import grpc
import threading

from ai.protos.sensors_pb2 import (
    SensorData, SensorType, CalibrationType, HealthStatus,
    MycelialProbeData, AcousticPestMonitorData, PestClassification,
    CalibrationRequest, CalibrationResponse, EmergencyShutdownRequest
)
from ai.protos.sensors_pb2_grpc import (
    MycelialProbeServiceStub, AcousticPestMonitorServiceStub,
    SensorManagementServiceStub
)
from ai.protos.robotics_pb2 import (
    RoboticCommand, CommandType, NavigationCommand, HarvestCommand,
    MaintenanceCommand, RoboticStatus, FleetStatus
)
from ai.protos.robotics_pb2_grpc import (
    AegisRoverServiceStub, AgriSwarmServiceStub, CanopyDroneServiceStub
)

logger = logging.getLogger(__name__)

class MockSensorSimulator:
    """Base class for sensor simulators that generate realistic test data"""

    def __init__(self, sensor_id: str, sensor_type: SensorType, zone_id: int = 1):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.zone_id = zone_id
        self.position = {"x": random.uniform(0, 100), "y": random.uniform(0, 100), "z": random.uniform(0, 5)}
        self.battery_level = 100.0
        self.signal_strength = 95.0
        self.is_online = True
        self.last_reading = None

    def generate_sensor_data(self) -> SensorData:
        """Generate realistic sensor data based on sensor type"""
        raise NotImplementedError

    def update_status(self):
        """Update sensor status (battery, signal, etc.)"""
        # Simulate battery drain
        self.battery_level = max(0, self.battery_level - random.uniform(0.01, 0.1))

        # Simulate signal variation
        self.signal_strength = max(0, min(100, self.signal_strength + random.uniform(-5, 5)))

        # Occasionally go offline
        if random.random() < 0.02:  # 2% chance
            self.is_online = not self.is_online

class MockMycelialProbe(MockSensorSimulator):
    """Simulator for Sub-Surface Mycelial Probes"""

    def __init__(self, sensor_id: str, zone_id: int = 1):
        super().__init__(sensor_id, SensorType.MYCELIAL_PROBE, zone_id)
        self.biomass_density = 0.5
        self.ph_level = 6.5
        self.electrical_activity = 0.1
        self.nutrient_levels = {"n": 25.0, "p": 15.0, "k": 20.0}

    def generate_sensor_data(self) -> SensorData:
        # Simulate realistic mycelial data changes
        self.biomass_density += random.uniform(-0.05, 0.05)
        self.biomass_density = max(0, min(1.0, self.biomass_density))

        self.ph_level += random.uniform(-0.2, 0.2)
        self.ph_level = max(4.0, min(8.0, self.ph_level))

        self.electrical_activity += random.uniform(-0.02, 0.02)
        self.electrical_activity = max(0, min(0.5, self.electrical_activity))

        # Update nutrient levels
        for nutrient in self.nutrient_levels:
            self.nutrient_levels[nutrient] += random.uniform(-2, 2)
            self.nutrient_levels[nutrient] = max(0, min(50, self.nutrient_levels[nutrient]))

        self.last_reading = time.time()

        mycelial_data = MycelialProbeData(
            biomass_density=self.biomass_density,
            ph_level=self.ph_level,
            electrical_activity=self.electrical_activity,
            nutrient_levels=self.nutrient_levels
        )

        return SensorData(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            zone_id=self.zone_id,
            position=self.position,
            timestamp=int(time.time() * 1000),
            mycelial_probe_data=mycelial_data,
            battery_level=self.battery_level,
            signal_strength=self.signal_strength
        )

class MockAcousticPestMonitor(MockSensorSimulator):
    """Simulator for Acoustic Pest Monitors"""

    def __init__(self, sensor_id: str, zone_id: int = 1):
        super().__init__(sensor_id, SensorType.ACOUSTIC_MONITOR, zone_id)
        self.frequency_spectrum = {}
        self.pest_activity_level = 0.0
        self.dominant_frequency = 0.0
        self.pest_classifications = []

    def generate_sensor_data(self) -> SensorData:
        # Simulate pest activity patterns
        self.pest_activity_level = random.uniform(0, 1.0)

        # Generate frequency spectrum
        self.frequency_spectrum = {}
        for freq in range(1000, 10000, 500):  # 1kHz to 10kHz range
            if random.random() < 0.3:  # 30% chance of activity at each frequency
                self.frequency_spectrum[str(freq)] = random.uniform(0, 100)

        # Determine dominant frequency
        if self.frequency_spectrum:
            self.dominant_frequency = float(max(self.frequency_spectrum.keys(),
                                              key=lambda k: self.frequency_spectrum[k]))

        # Generate pest classifications based on activity
        self.pest_classifications = []
        if self.pest_activity_level > 0.7:
            pest_types = ["aphid", "beetle", "caterpillar", "whitefly", "thrips"]
            num_pests = random.randint(1, 3)
            for _ in range(num_pests):
                pest_type = random.choice(pest_types)
                confidence = random.uniform(0.6, 0.95)
                self.pest_classifications.append(PestClassification(
                    pest_type=pest_type,
                    confidence=confidence,
                    activity_level=self.pest_activity_level
                ))

        self.last_reading = time.time()

        acoustic_data = AcousticPestMonitorData(
            frequency_spectrum=self.frequency_spectrum,
            pest_activity_level=self.pest_activity_level,
            dominant_frequency=self.dominant_frequency,
            pest_classifications=self.pest_classifications
        )

        return SensorData(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            zone_id=self.zone_id,
            position=self.position,
            timestamp=int(time.time() * 1000),
            acoustic_pest_data=acoustic_data,
            battery_level=self.battery_level,
            signal_strength=self.signal_strength
        )

class MockRoboticClient:
    """Base class for mock robotic clients"""

    def __init__(self, robot_id: str, robot_type: str, stub_class):
        self.robot_id = robot_id
        self.robot_type = robot_type
        self.stub_class = stub_class
        self.channel = None
        self.stub = None
        self.is_connected = False
        self.status = "offline"
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.battery_level = 100.0
        self.task_queue = []
        self.current_task = None

    def connect(self, host: str = "localhost", port: int = 50051):
        """Connect to gRPC service"""
        try:
            self.channel = grpc.insecure_channel(f"{host}:{port}")
            self.stub = self.stub_class(self.channel)
            self.is_connected = True
            self.status = "idle"
            logger.info(f"{self.robot_type} {self.robot_id} connected to {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect {self.robot_type} {self.robot_id}: {e}")
            self.is_connected = False

    def disconnect(self):
        """Disconnect from gRPC service"""
        if self.channel:
            self.channel.close()
        self.is_connected = False
        self.status = "offline"
        logger.info(f"{self.robot_type} {self.robot_id} disconnected")

    def update_status(self):
        """Update robotic status"""
        self.battery_level = max(0, self.battery_level - random.uniform(0.1, 0.5))

        # Simulate position changes if moving
        if self.status == "moving":
            self.position["x"] += random.uniform(-1, 1)
            self.position["y"] += random.uniform(-1, 1)
            self.position["z"] += random.uniform(-0.1, 0.1)

    def execute_command(self, command: RoboticCommand):
        """Execute a robotic command"""
        raise NotImplementedError

class MockAegisRover(MockRoboticClient):
    """Mock Aegis Rover client"""

    def __init__(self, robot_id: str):
        super().__init__(robot_id, "AegisRover", AegisRoverServiceStub)
        self.payload_capacity = 50.0  # kg
        self.current_payload = 0.0
        self.wheel_efficiency = 0.95

    def execute_command(self, command: RoboticCommand):
        """Execute rover-specific commands"""
        if command.command_type == CommandType.NAVIGATE:
            self.status = "moving"
            # Simulate navigation to target
            time.sleep(random.uniform(1, 3))  # Simulate movement time
            self.position = dict(command.navigation_command.target_position)
            self.status = "idle"
            return {"status": "completed", "position": self.position}

        elif command.command_type == CommandType.HARVEST:
            self.status = "harvesting"
            # Simulate harvesting operation
            time.sleep(random.uniform(2, 5))
            harvested_amount = random.uniform(5, 15)
            self.current_payload += harvested_amount
            self.status = "idle"
            return {"status": "completed", "harvested": harvested_amount}

        elif command.command_type == CommandType.MAINTAIN:
            self.status = "maintenance"
            # Simulate maintenance operation
            time.sleep(random.uniform(1, 2))
            self.wheel_efficiency = min(1.0, self.wheel_efficiency + 0.05)
            self.status = "idle"
            return {"status": "completed", "maintenance": "wheel_calibration"}

class MockAgriSwarmBot(MockRoboticClient):
    """Mock Agri-Swarm Micro-Bot client"""

    def __init__(self, robot_id: str):
        super().__init__(robot_id, "AgriSwarmBot", AgriSwarmServiceStub)
        self.swarm_id = f"swarm_{random.randint(1, 5)}"
        self.coordination_state = "independent"
        self.sensor_range = 2.0  # meters

    def execute_command(self, command: RoboticCommand):
        """Execute swarm bot commands"""
        if command.command_type == CommandType.NAVIGATE:
            self.status = "moving"
            time.sleep(random.uniform(0.5, 1.5))
            self.position = dict(command.navigation_command.target_position)
            self.status = "idle"
            return {"status": "completed", "position": self.position}

        elif command.command_type == CommandType.HARVEST:
            self.status = "harvesting"
            time.sleep(random.uniform(0.5, 2))
            harvested_amount = random.uniform(0.1, 1.0)
            self.status = "idle"
            return {"status": "completed", "harvested": harvested_amount}

class MockCanopyDrone(MockRoboticClient):
    """Mock Canopy Drone client"""

    def __init__(self, robot_id: str):
        super().__init__(robot_id, "CanopyDrone", CanopyDroneServiceStub)
        self.altitude = 0.0
        self.camera_resolution = "4K"
        self.flight_time_remaining = 25.0  # minutes

    def execute_command(self, command: RoboticCommand):
        """Execute drone commands"""
        if command.command_type == CommandType.NAVIGATE:
            self.status = "flying"
            time.sleep(random.uniform(1, 2))
            self.position = dict(command.navigation_command.target_position)
            self.altitude = self.position.get("z", 0)
            self.flight_time_remaining -= random.uniform(0.5, 1.5)
            self.status = "hovering"
            return {"status": "completed", "position": self.position, "altitude": self.altitude}

        elif command.command_type == CommandType.HARVEST:
            # Drones don't harvest, but can survey
            self.status = "surveying"
            time.sleep(random.uniform(1, 3))
            survey_data = {
                "canopy_density": random.uniform(0.3, 0.9),
                "plant_health_score": random.uniform(0.5, 1.0),
                "pest_detected": random.choice([True, False])
            }
            self.status = "hovering"
            return {"status": "completed", "survey": survey_data}

class SensorSimulatorManager:
    """Manages multiple sensor simulators"""

    def __init__(self):
        self.simulators: Dict[str, MockSensorSimulator] = {}
        self.running = False
        self.thread = None

    def add_simulator(self, simulator: MockSensorSimulator):
        """Add a sensor simulator"""
        self.simulators[simulator.sensor_id] = simulator

    def start_simulation(self, update_interval: float = 1.0):
        """Start all simulators"""
        self.running = True
        self.thread = threading.Thread(target=self._simulation_loop, args=(update_interval,))
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Started simulation with {len(self.simulators)} sensors")

    def stop_simulation(self):
        """Stop all simulators"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Stopped sensor simulation")

    def _simulation_loop(self, update_interval: float):
        """Main simulation loop"""
        while self.running:
            for simulator in self.simulators.values():
                simulator.update_status()
            time.sleep(update_interval)

    def get_sensor_data(self, sensor_id: str) -> Optional[SensorData]:
        """Get current data from a specific sensor"""
        simulator = self.simulators.get(sensor_id)
        if simulator:
            return simulator.generate_sensor_data()
        return None

    def get_all_sensor_data(self) -> List[SensorData]:
        """Get data from all sensors"""
        return [simulator.generate_sensor_data() for simulator in self.simulators.values()]

class RoboticFleetManager:
    """Manages mock robotic fleet"""

    def __init__(self):
        self.robots: Dict[str, MockRoboticClient] = {}
        self.running = False
        self.thread = None

    def add_robot(self, robot: MockRoboticClient):
        """Add a robot to the fleet"""
        self.robots[robot.robot_id] = robot

    def connect_all(self, host: str = "localhost", port: int = 50051):
        """Connect all robots"""
        for robot in self.robots.values():
            robot.connect(host, port)

    def disconnect_all(self):
        """Disconnect all robots"""
        for robot in self.robots.values():
            robot.disconnect()

    def start_fleet_simulation(self, update_interval: float = 2.0):
        """Start fleet status updates"""
        self.running = True
        self.thread = threading.Thread(target=self._fleet_loop, args=(update_interval,))
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Started fleet simulation with {len(self.robots)} robots")

    def stop_fleet_simulation(self):
        """Stop fleet simulation"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Stopped robotic fleet simulation")

    def _fleet_loop(self, update_interval: float):
        """Main fleet update loop"""
        while self.running:
            for robot in self.robots.values():
                robot.update_status()
            time.sleep(update_interval)

    def get_fleet_status(self) -> Dict[str, Any]:
        """Get overall fleet status"""
        total_robots = len(self.robots)
        online_robots = sum(1 for r in self.robots.values() if r.is_connected)
        active_robots = sum(1 for r in self.robots.values() if r.status not in ["idle", "offline"])

        return {
            "total_robots": total_robots,
            "online_robots": online_robots,
            "active_robots": active_robots,
            "fleet_efficiency": online_robots / total_robots if total_robots > 0 else 0,
            "robots": [
                {
                    "id": robot.robot_id,
                    "type": robot.robot_type,
                    "status": robot.status,
                    "connected": robot.is_connected,
                    "battery": robot.battery_level,
                    "position": robot.position
                }
                for robot in self.robots.values()
            ]
        }