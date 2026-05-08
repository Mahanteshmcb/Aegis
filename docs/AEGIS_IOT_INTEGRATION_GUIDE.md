# Aegis IoT & Robotics Integration Guide

**Author:** Aegis Development Team  
**Date:** May 2026  
**Version:** 1.0  
**Status:** Production Documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Hardware Stack](#hardware-stack)
3. [Arduino Integration (Sensors & IoT)](#arduino-integration)
4. [ROS 2 Humble Integration (Autonomous Robots)](#ros-2-humble-integration)
5. [Drone SDK Integration](#drone-sdk-integration)
6. [Communication Protocols](#communication-protocols)
7. [Data Flow Architecture](#data-flow-architecture)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Deployment Guide](#deployment-guide)

---

## Overview

Aegis is a distributed agricultural robotics platform supporting three tiers of connected devices:

| Tier | Hardware | Software | Use Case |
|------|----------|----------|----------|
| **IoT Sensors** | Arduino-based microcontrollers | Custom firmware (C/C++) | Environmental monitoring |
| **Ground Robots** | Raspberry Pi + ROS 2 Humble | Python + ROS 2 nodes | Autonomous field operations |
| **Aerial Robots** | Commercial drones (DJI, Freefly) | Manufacturer SDK + Python wrapper | Aerial surveys, surveillance |

All devices communicate with **Aegis Backend (FastAPI)** for centralized coordination, and **RoboticsService (gRPC)** for fleet management.

---

## Hardware Stack

### 1. Arduino for IoT Sensors

#### **Recommended Hardware**

```
Device:          Arduino MKR WiFi 1010 or Arduino MKR NB-IoT 1500
├─ Processor:    SAMD21 (32-bit ARM Cortex-M0+)
├─ RAM:          32 KB
├─ Flash:        256 KB
├─ Connectivity: WiFi (1010) / NB-IoT (1500) / LoRaWAN
├─ Power:        3.3V, ~60-80 mA
├─ Cost:         $40-60 per unit
└─ Ecosystem:    Arduino IDE, extensive sensor libraries

Common Sensors:
├─ Temperature/Humidity:  DHT22 ($3-5)
├─ Soil Moisture:        Capacitive sensor ($5-10)
├─ Light Level:          BH1750 ($2-3)
├─ Pressure:             BMP280 ($2-3)
├─ Water Flow:           YF-S201 ($10-15)
├─ pH Sensor:            Analog pH meter ($15-20)
└─ CO2 Sensor:           MH-Z19 ($20-30)

Connectivity Options:
├─ WiFi:      Direct connection to Aegis backend / MQTT broker
├─ LoRaWAN:   Long-range, low-power (range: 10+ km)
├─ NB-IoT:    Cellular, always-on (requires carrier plan)
└─ Bluetooth: Short-range to local gateway (Raspberry Pi)
```

#### **Software Environment**

```
IDE:           Arduino IDE 2.0 or PlatformIO
Language:      C/C++ (Arduino flavor)
Libraries:     WiFi, MQTT (PubSubClient), JSON (ArduinoJson)
Firmware:      Custom sketches (< 100 KB typical)
OTA Updates:   Supported via MQTT or HTTP endpoints
```

#### **Typical Arduino Sensor Node**

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// Configuration
const char* SSID = "farm_network";
const char* PASSWORD = "secure_password";
const char* MQTT_BROKER = "192.168.1.100";
const int MQTT_PORT = 1883;
const char* DEVICE_ID = "SENSOR_SOIL_01";

// Hardware
#define DHT_PIN D4
DHT dht(DHT_PIN, DHT22);
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

void setup() {
    Serial.begin(115200);
    dht.begin();
    
    // Connect WiFi
    WiFi.begin(SSID, PASSWORD);
    while (WiFi.status() != WL_CONNECTED) delay(500);
    
    // Connect MQTT
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.connect(DEVICE_ID);
}

void loop() {
    // Read sensors
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    
    // Create JSON payload
    DynamicJsonDocument doc(256);
    doc["device_id"] = DEVICE_ID;
    doc["temperature"] = temperature;
    doc["humidity"] = humidity;
    doc["timestamp"] = millis();
    
    // Publish to MQTT
    char buffer[256];
    serializeJson(doc, buffer);
    mqttClient.publish("sensors/greenhouse/data", buffer);
    
    delay(30000); // Every 30 seconds
}
```

---

### 2. ROS 2 Humble for Autonomous Robots

#### **Recommended Hardware**

```
Base Platform:   Clearpath Ridgeback / Custom Raspberry Pi rover
├─ Compute:      Jetson Xavier NX ($400) or Jetson Orin Nano ($200)
├─ RAM:          8-16 GB
├─ Storage:      NVMe SSD (256 GB+)
├─ Sensors:      
│   ├─ LiDAR:    RPLIDAR A2M8 ($100) or OS1-32 ($4000)
│   ├─ Camera:   Realsense D435i ($180) or Luxonis OAK-D Pro ($200)
│   ├─ IMU:      BNO055 ($20-30)
│   └─ Encoders: Wheel encoder on each motor
├─ Actuators:
│   ├─ Motors:   12V brushed DC + encoder feedback
│   ├─ Pump:     12V solenoid (spray system)
│   └─ Gripper:  Servo-based (optional)
├─ Power:        24V lithium battery (8S) + BMS
├─ Connectivity: WiFi 6 (802.11ax) + Ethernet fallback
├─ OS:           Ubuntu 22.04 LTS
└─ Total Cost:   $1500-3000 per robot (DIY)
```

#### **Software Environment**

```
OS:              Ubuntu 22.04 LTS (arm64)
ROS Version:     ROS 2 Humble (LTS until 2027)
Build System:    colcon
Language:        Python 3.10 + C++
Key Packages:
├─ nav2:         Navigation stack (path planning, SLAM)
├─ ros2_control: Motor control framework
├─ sensor_fusion: Multi-sensor integration
├─ image_proc:   Camera processing
└─ visualization: RViz for debugging

Middleware:      DDS (Fast-RTPS default)
Communication:   ROS 2 services, topics, actions
```

#### **ROS 2 Node Structure**

```
rover_bringup/
├─ launch/
│   ├─ robot.launch.py       # Main launch file
│   ├─ sensors.launch.py     # LiDAR, camera, IMU
│   └─ navigation.launch.py  # Nav2 stack
├─ config/
│   ├─ nav2_params.yaml      # Navigation parameters
│   ├─ controller.yaml       # Motor PID tuning
│   └─ sensors.yaml          # Calibration
├─ scripts/
│   ├─ motor_controller.py   # Motor PWM control
│   ├─ sensor_fusion.py      # Multi-sensor integration
│   ├─ task_executor.py      # Execute Aegis tasks
│   └─ status_publisher.py   # Publish to Aegis
└─ CMakeLists.txt

Key ROS 2 Nodes:
├─ motor_controller_node:    Listen to motor commands, drive wheels/pump
├─ sensor_fusion_node:       Fuse LiDAR + IMU + encoder data
├─ nav2_bringup:            Navigation (already packaged)
├─ aegis_bridge_node:        Convert REST/gRPC ↔ ROS 2
└─ task_executor_node:       Execute SPRAY/PLANT/INSPECT tasks
```

#### **Example ROS 2 Task Executor Node**

```python
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.executors import MultiThreadedExecutor
import requests
import json

from my_robot_interfaces.action import ExecuteTask
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32

class AegisTaskExecutor(Node):
    def __init__(self):
        super().__init__('aegis_task_executor')
        
        self.robot_id = "ROVER_001"
        self.api_base = "http://aegis-backend:8000/api/v1"
        self.jwt_token = self.authenticate()
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pump_pub = self.create_publisher(Float32, '/pump_speed', 10)
        
        # Action server for executing Aegis tasks
        self._action_server = ActionServer(
            self,
            ExecuteTask,
            'execute_task',
            self.execute_task_callback
        )
        
        # Subscribe to Aegis task queue
        self.create_timer(5.0, self.poll_aegis_tasks)
    
    def authenticate(self):
        """Get JWT token from Aegis"""
        response = requests.post(
            f"{self.api_base}/auth/login",
            json={"email": "rover@aegis.farm", "password": "secret"}
        )
        return response.json()["access_token"]
    
    def poll_aegis_tasks(self):
        """Periodically check for new tasks from Aegis"""
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        response = requests.get(
            f"{self.api_base}/robotics/active",
            headers=headers
        )
        # Process tasks...
    
    def execute_task_callback(self, goal_handle):
        """Execute a task from Aegis"""
        task = goal_handle.request
        
        if task.operation_type == "SPRAY":
            self.execute_spray(task)
        elif task.operation_type == "NAVIGATE":
            self.execute_navigate(task)
        elif task.operation_type == "INSPECT":
            self.execute_inspect(task)
        
        goal_handle.succeed()
    
    def execute_spray(self, task):
        """Execute spray operation"""
        self.get_logger().info(f"Starting spray task: {task.task_id}")
        
        # Activate pump
        pump_msg = Float32()
        pump_msg.data = 0.8  # 80% speed
        self.pump_pub.publish(pump_msg)
        
        # Navigate to target zone
        target = json.loads(task.task_detail)
        self.navigate_to(target["target_zone"])
        
        # Spray for duration
        duration = target["spray_volume"] / 10  # 10 L/min
        rclpy.spin_once(self, timeout_sec=duration)
        
        # Deactivate pump
        pump_msg.data = 0.0
        self.pump_pub.publish(pump_msg)
        
        # Report status
        self.report_task_completion(task.task_id, "SUCCESS")
    
    def navigate_to(self, target_zone):
        """Use nav2 to navigate to target"""
        # Use ROS 2 Actions to communicate with nav2
        pass
    
    def execute_inspect(self, task):
        """Inspect crops and take photos"""
        # Use camera node to capture images
        # Send images to Aegis for AI analysis
        pass
    
    def report_task_completion(self, task_id, status):
        """Report back to Aegis"""
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        requests.post(
            f"{self.api_base}/robotics/sensor-data",
            json={
                "robot_id": self.robot_id,
                "health": {"battery": 75, "cpu_temp": 55},
                "observations": {"task_id": task_id, "status": status}
            },
            headers=headers
        )

def main(args=None):
    rclpy.init(args=args)
    executor = AegisTaskExecutor()
    executor = MultiThreadedExecutor()
    rclpy.spin(executor)

if __name__ == '__main__':
    main()
```

---

### 3. Drone SDK Integration

#### **Supported Drone Platforms**

| Drone | SDK | Language | Features |
|-------|-----|----------|----------|
| **DJI Matrice 300** | DJI SDK | Python / C++ | Payload mount, industrial-grade |
| **DJI Phantom 4 RTK** | DJI PSDK | Python / C | RTK positioning (2cm accuracy) |
| **Freefly Astro** | Freefly SDK | Python | 55 lbs payload, cinema grade |
| **Auterion Skynode** | MAVLink | Python | Open-source, industry standard |

#### **DJI Integration Example (Most Common)**

```
Hardware:
├─ Drone:           DJI Matrice 300 RTK ($15,000)
├─ Payload:         Zenmuse P1 camera (45MP) + RTK module
├─ Battery:         3x TB65 batteries (5 flights per charge)
├─ Remote:          Standard DJI RC Plus
├─ Compute:         Onboard (Snap 855) or Ground station (GPU PC)
└─ Connectivity:    OcuSync Enterprise (WiFi 6) + 4G/5G module

Software Environment:
├─ SDK:           DJI PSDK (Payload SDK) or DJI SDK
├─ Language:      Python 3.8+ (preferred)
├─ API:           RESTful + WebSocket
├─ Libraries:     dji-sdk-python, opencv-python, pillow
├─ Simulator:     DJI FlightSimulator for testing
└─ License:       Free for non-commercial, pay-for-commercial

Typical Flow:
├─ Drone takeoff (automatic)
├─ Navigate via waypoint list
├─ Take photos at each waypoint
├─ Land automatically
└─ Upload photos to Aegis for analysis
```

#### **Python Wrapper for DJI Drone**

```python
#!/usr/bin/env python3

import requests
import dji_sdk
import logging

class AegisDroneIntegration:
    def __init__(self, drone_id, api_base_url):
        self.drone_id = drone_id
        self.api_base = api_base_url
        self.jwt_token = self.authenticate()
        
        # Initialize DJI SDK
        self.dji = dji_sdk.DJIFleet()
        self.dji.login("DJI_API_KEY", "DJI_SECRET")
    
    def authenticate(self):
        """Authenticate with Aegis backend"""
        response = requests.post(
            f"{self.api_base}/auth/login",
            json={"email": "drone@aegis.farm", "password": "secret"}
        )
        return response.json()["access_token"]
    
    def register_drone(self):
        """Register drone with Aegis"""
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        requests.post(
            f"{self.api_base}/robotics/register",
            json={
                "robot_id": self.drone_id,
                "robot_type": "CANOPY_DRONE",
                "firmware_version": "1.2.3",
                "model_year": 2025,
                "capabilities": ["INSPECT", "SURVEY", "SAMPLE"]
            },
            headers=headers
        )
    
    def execute_survey_mission(self, task):
        """Execute aerial survey mission"""
        task_detail = json.loads(task.task_detail)
        
        # Create waypoint mission
        mission = {
            "drone_id": self.drone_id,
            "waypoints": task_detail["waypoints"],
            "altitude": task_detail.get("altitude", 100),  # meters
            "speed": task_detail.get("speed", 5),  # m/s
            "camera_settings": {
                "interval": 2,  # Photo every 2 seconds
                "mode": "PHOTO"
            }
        }
        
        # Upload mission to drone
        self.dji.upload_mission(mission)
        
        # Start mission
        self.dji.start_mission()
        
        # Wait for completion
        while not self.dji.is_mission_complete():
            status = self.dji.get_mission_status()
            self.report_progress(task.task_id, status)
            time.sleep(5)
        
        # Download photos
        photos = self.dji.download_photos()
        
        # Upload to Aegis for analysis
        self.upload_photos_to_aegis(task.task_id, photos)
        
        # Report completion
        self.report_task_completion(task.task_id, "SUCCESS")
    
    def upload_photos_to_aegis(self, task_id, photos):
        """Upload aerial photos to Aegis for AI analysis"""
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        
        for i, photo_path in enumerate(photos):
            with open(photo_path, 'rb') as f:
                files = {'file': f}
                requests.post(
                    f"{self.api_base}/research/upload",
                    files=files,
                    data={"task_id": task_id, "order": i},
                    headers={"Authorization": f"Bearer {self.jwt_token}"}
                )
    
    def report_task_completion(self, task_id, status):
        """Report back to Aegis"""
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        requests.post(
            f"{self.api_base}/robotics/sensor-data",
            json={
                "robot_id": self.drone_id,
                "health": {"battery": 100, "gps_sats": 15},
                "observations": {"task_id": task_id, "status": status}
            },
            headers=headers
        )
```

---

## Communication Protocols

### Protocol Comparison

```
┌─────────────────────────────────────────────────────────────┐
│            COMMUNICATION PROTOCOL MATRIX                    │
└─────────────────────────────────────────────────────────────┘

Use Case: Arduino → Aegis
├─ MQTT (Recommended)
│  ├─ Latency:    100ms - 1s
│  ├─ Throughput: < 1 Mbps
│  ├─ Power:      Low (~50 mA)
│  ├─ Range:      WiFi (~100m)
│  └─ Reliability: QoS 1-2 available
├─ HTTP REST (Alternative)
│  ├─ Latency:    200ms - 2s
│  ├─ Throughput: < 100 Kbps
│  ├─ Power:      Medium (~100 mA)
│  ├─ Range:      WiFi (~100m)
│  └─ Reliability: HTTP retries needed
└─ LoRaWAN (Long-range)
   ├─ Latency:    1-10s
   ├─ Throughput: ~50 bps
   ├─ Power:      Very low (<10 mA)
   ├─ Range:      10+ km
   └─ Reliability: Built-in ACK

Use Case: ROS 2 Robot → Aegis
├─ gRPC (Recommended)
│  ├─ Latency:    10-50ms
│  ├─ Throughput: 10-100 Mbps
│  ├─ Power:      High (~500 mA)
│  ├─ Range:      WiFi 6 (~50m)
│  └─ Reliability: HTTP/2 multiplexing
└─ ROS 2 DDS (Internal robot only)
   ├─ Latency:    1-5ms
   ├─ Throughput: 100+ Mbps
   ├─ Power:      Medium (~200 mA)
   ├─ Range:      WiFi (~30m)
   └─ Reliability: QoS policies available

Use Case: Drone → Aegis
├─ Manufacturer SDK WebSocket
│  ├─ Latency:    100-500ms
│  ├─ Throughput: 1-10 Mbps
│  ├─ Power:      Powered platform
│  ├─ Range:      4G/5G or WiFi
│  └─ Reliability: Vendor managed
└─ REST API (Fallback)
   ├─ Latency:    1-2s
   ├─ Throughput: < 1 Mbps
   ├─ Power:      Powered platform
   ├─ Range:      4G/5G or WiFi
   └─ Reliability: Manual retry logic
```

### Network Architecture

```
WiFi Access Points (2x Ubiquiti UniFi):
├─ Coverage:     5GHz for robots (high throughput)
│                2.4GHz for Arduino (wider range)
├─ Backhaul:     Ethernet to main gateway
└─ Security:     WPA3 with VLAN isolation

MQTT Broker (Mosquitto on Raspberry Pi):
├─ Address:      192.168.1.100:1883
├─ Topics:
│   ├─ sensors/+/data        (Arduino → Broker)
│   ├─ robots/+/commands     (Aegis → Robot)
│   ├─ robots/+/status       (Robot → Aegis)
│   └─ drones/+/telemetry    (Drone → Aegis)
├─ Persistence: Retained messages for critical commands
└─ ACL:         Per-device authentication

Main Gateway (Raspberry Pi 4):
├─ Runs:         MQTT broker, sensor aggregator
├─ Connectivity: Ethernet (gigabit) + 4G backup
├─ Storage:      SSD for sensor logs
└─ Services:     IP forwarding, firewall, VPN

Aegis Backend Server:
├─ Location:     Cloud (AWS/GCP) or On-prem
├─ API:          FastAPI on port 8000
├─ Database:     PostgreSQL for production
├─ gRPC:         Port 50051 (Vryndara), 50052 (Robotics)
└─ Security:     HTTPS, JWT, CORS
```

---

## Data Flow Architecture

### Sensor Data Ingestion

```
Arduino DHT22 Sensor
  ↓
  └─ Measure: temp=22.5°C, humidity=65%
  ↓
  └─ Publish MQTT: sensors/greenhouse/temp
  ↓
  └─ MQTT Broker receives
  ↓
  └─ Python Subscriber (on gateway)
  ↓
  └─ Convert to JSON: {"sensor_id": 42, "value": 22.5, "unit": "C"}
  ↓
  └─ POST /api/v1/sensors/data (HTTP REST)
  ↓
  └─ Aegis Backend validates JWT token
  ↓
  └─ Store in PostgreSQL:
     └─ SensorData table
        ├─ sensor_id: 42
        ├─ value: 22.5
        ├─ unit: "C"
        ├─ timestamp: 2025-05-09 14:30:00
        └─ zone_id: 3
  ↓
  └─ Dashboard queries historical data
     └─ GET /api/v1/sensors/42/data?limit=100
     └─ Returns: [{timestamp, value, unit}, ...]
```

### Task Execution Flow

```
User clicks "Spray Field" in Dashboard
  ↓
  └─ Frontend sends: POST /api/v1/robotics/tasks
  ↓
  ├─ Aegis validates: user role, robot exists, task valid
  ↓
  ├─ Store in DB: RoboticTask (status=PENDING)
  ↓
  ├─ Call gRPC RoboticsService.SendTask(...)
  ↓
  ├─ RoboticsService publishes MQTT to robot
  ├─ Topic: robots/ROVER_001/commands
  ├─ Payload: {"action": "SPRAY", "zone_id": 3, "volume": 50}
  ↓
  ├─ ROS 2 robot receives via MQTT subscription
  ↓
  ├─ Execute task:
  │  ├─ Activate pump
  │  ├─ Navigate to zone (via Nav2)
  │  ├─ Spray for duration
  │  └─ Deactivate pump
  ↓
  ├─ Robot publishes status: robots/ROVER_001/status
  ├─ Payload: {"task_id": "xxx", "status": "COMPLETED"}
  ↓
  ├─ MQTT Subscriber (gateway) forwards to Aegis
  ├─ POST /api/v1/robotics/sensor-data
  ↓
  ├─ Aegis updates DB: RoboticTask (status=COMPLETED)
  ↓
  └─ Dashboard shows: "Task Completed ✓"
```

---

## Implementation Roadmap

### Phase 1: Single Arduino Sensor (Week 1)

```
Task 1: Hardware Setup
├─ Arduino MKR WiFi 1010 + DHT22 sensor
├─ Connect to development WiFi
└─ Verify Serial output

Task 2: Arduino Sketch
├─ WiFi connection code
├─ DHT22 reading loop
├─ MQTT publish function
└─ Deploy and test (every 30 seconds)

Task 3: Test Integration
├─ MQTT broker logs (mosquitto logs)
├─ Aegis receives sensor data
├─ Verify DB storage
└─ Query via REST API
```

### Phase 2: Multi-Sensor Network (Week 2-3)

```
Task 1: Deploy 5 Arduino nodes
├─ Different sensor types (temp, humidity, soil, light, water)
├─ Assign unique device IDs
├─ Register in Aegis DB
└─ Configure MQTT topics

Task 2: Data Aggregation
├─ Implement sensor fusion (multi-sensor readings → insights)
├─ Example: soil_moisture + rainfall + temperature → irrigation trigger
├─ Store derived metrics in DB
└─ Expose via REST API

Task 3: Dashboard Visualization
├─ Real-time sensor charts
├─ Historical trends
├─ Alert thresholds
└─ Export to CSV
```

### Phase 3: ROS 2 Robot Deployment (Week 4-6)

```
Task 1: Hardware Assembly
├─ Raspberry Pi + Jetson Nano stack
├─ LiDAR + Camera mount
├─ Motor driver + power distribution
├─ Battery management system
└─ Enclosure weatherproofing

Task 2: ROS 2 Humble Setup
├─ Ubuntu 22.04 installation
├─ ROS 2 Humble packages
├─ Navigation stack (Nav2)
├─ Sensor drivers (LiDAR, camera, IMU)
└─ Motor control node

Task 3: ROS 2 ↔ Aegis Bridge
├─ Create aegis_bridge_node
├─ Task executor node
├─ Status publisher node
├─ Listen for commands via gRPC
└─ Execute and report back

Task 4: Field Testing
├─ Manual control via Aegis dashboard
├─ Autonomous navigation test
├─ Sensor fusion validation
└─ Document performance metrics
```

### Phase 4: Drone Integration (Week 7-8)

```
Task 1: Drone Setup
├─ DJI Matrice 300 RTK unboxing
├─ Battery charging + firmware update
├─ Camera calibration
├─ Flight simulator practice
└─ Insurance + permits

Task 2: SDK Integration
├─ DJI PSDK installation
├─ Authenticate with DJI Cloud
├─ Create mission planning script
├─ Implement photo download
└─ Test in simulator

Task 3: Aegis Integration
├─ Register drone with robotics service
├─ Create survey mission template
├─ Implement photo upload to Aegis
├─ Call AI inference on photos
└─ Store results in DB

Task 4: Field Operations
├─ Plan survey mission (waypoints)
├─ Launch drone
├─ Monitor mission in real-time
├─ Retrieve and analyze photos
└─ Generate crop health report
```

---

## Deployment Guide

### Single-Machine Setup (Development)

```bash
# 1. Aegis Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# 2. RoboticsService (gRPC)
cd ../ai
python robotics_service.py  # Runs on port 50052

# 3. MQTT Broker (Mosquitto)
docker run -d --name mosquitto \
  -p 1883:1883 \
  -v /path/to/mosquitto.conf:/mosquitto/config/mosquitto.conf \
  eclipse-mosquitto

# 4. Arduino Sketch
# Upload to Arduino via IDE with WiFi credentials

# 5. ROS 2 Robot (if available)
cd robot_bringup
colcon build
source install/setup.bash
ros2 launch robot bringup.launch.py
```

### Production Multi-Server Setup

```
Server 1: Aegis Backend
├─ OS: Ubuntu 22.04 LTS
├─ CPU: 8-core
├─ RAM: 16 GB
├─ Storage: SSD 500 GB
├─ Services:
│   ├─ FastAPI (port 8000)
│   ├─ PostgreSQL (port 5432)
│   ├─ Redis (caching)
│   └─ nginx (reverse proxy)
└─ Networking: Gigabit Ethernet + 4G backup

Server 2: RoboticsService + MQTT Broker
├─ OS: Ubuntu 22.04 LTS
├─ CPU: 4-core
├─ RAM: 8 GB
├─ Services:
│   ├─ gRPC Server (port 50052)
│   ├─ Mosquitto MQTT (port 1883)
│   └─ Prometheus (monitoring)
└─ Networking: Gigabit Ethernet

Server 3: AI/ML (Vryndara)
├─ OS: Ubuntu 22.04 LTS
├─ GPU: NVIDIA RTX 3090
├─ CPU: 16-core
├─ RAM: 32 GB
├─ Services:
│   ├─ Vryndara gRPC (port 50051)
│   ├─ TensorFlow serving
│   └─ Model training pipelines
└─ Networking: Gigabit Ethernet

Network Gateway (Raspberry Pi 4)
├─ MQTT Broker (local sensor network)
├─ WiFi AP (Arduino + IoT devices)
├─ VPN tunnel to cloud backend
└─ Local logging & backup
```

### Docker Compose Stack

```yaml
version: '3.8'

services:
  aegis-backend:
    image: aegis-backend:latest
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/aegis
      ROBOTICS_HOST: robotics-service
    depends_on:
      - db
      - mqtt

  robotics-service:
    image: aegis-robotics-service:latest
    ports:
      - "50052:50052"
    environment:
      MQTT_BROKER: mqtt:1883

  mqtt:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: aegis
      POSTGRES_PASSWORD: secure_password
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

---

## Verification Checklist

Before deploying to production:

```
Arduino IoT Sensors:
├─ [ ] WiFi connectivity stable (WiFi power ≥ -70 dBm)
├─ [ ] Sensor readings accurate (verified with calibration standard)
├─ [ ] MQTT publishing every 30 seconds
├─ [ ] Power consumption < 150 mA
├─ [ ] Battery lasts > 30 days (with solar recharge)
└─ [ ] OTA firmware update capability working

ROS 2 Robot:
├─ [ ] Navigation tested in known environment
├─ [ ] Sensor fusion outputs stable (< 5% noise)
├─ [ ] Motor control responsive (< 100ms latency)
├─ [ ] Obstacle avoidance working
├─ [ ] Battery monitoring accurate
├─ [ ] gRPC bridge communicating with Aegis
├─ [ ] Task execution with > 95% success rate
└─ [ ] Emergency stop responds < 100ms

Drone Integration:
├─ [ ] Drone RTK positioning accurate (< 2cm error)
├─ [ ] Camera autofocus working
├─ [ ] Mission planning flexible (custom waypoints)
├─ [ ] Photo download reliable
├─ [ ] Flight time > 45 minutes
├─ [ ] WiFi 6 connectivity stable (range ≥ 2 km)
└─ [ ] AI inference on photos completes < 5s

System Integration:
├─ [ ] Multi-robot concurrent control works (10+ robots)
├─ [ ] Sensor data ingestion handles 100+ sensors
├─ [ ] Dashboard loads < 2 seconds
├─ [ ] API response times < 500ms
├─ [ ] Database query optimization complete
├─ [ ] Logging captures all errors
├─ [ ] Monitoring alerts configured
└─ [ ] Backup & recovery tested
```

---

## Support & Troubleshooting

### Common Arduino Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| WiFi won't connect | SSID/password wrong | Verify credentials in sketch |
| MQTT publish failing | Broker unreachable | Check broker IP and firewall |
| Sensor reads erratic | Noisy analog input | Add 0.1µF capacitor near sensor |
| Power consumption high | WiFi always on | Implement sleep mode when idle |

### Common ROS 2 Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Nav2 path planning slow | Map resolution too fine | Reduce costmap resolution |
| Sensor fusion unstable | Sensor calibration off | Recalibrate IMU & LiDAR |
| gRPC connection drops | Network latency high | Check WiFi signal strength |
| Motor jitter | PID tuning poor | Retune P/I/D constants |

### Common Drone Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| GPS RTK not converging | Too few satellites | Wait 60+ seconds, move to open sky |
| Camera gimbal drifting | Calibration needed | Run gimbal auto-calibration in DJI app |
| Photo quality dark | ISO too low | Increase ISO to 400-800 |
| Mission upload fails | Firmware out-of-date | Update drone firmware via DJI Assistant |

---

## References

- Arduino: https://docs.arduino.cc
- ROS 2 Humble: https://docs.ros.org/en/humble
- DJI SDK: https://developer.dji.com/doc
- Aegis Robotics API: `/api/v1/robotics/*`

---

**Last Updated:** May 9, 2026  
**Maintained By:** Aegis Development Team  
**Next Review:** August 9, 2026
