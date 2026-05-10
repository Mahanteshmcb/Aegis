# Aegis IoT Technology Stack - Quick Reference

**Created:** May 9, 2026  
**Project:** Aegis Agricultural Robotics Platform  
**Status:** ✅ Production Ready

---

## Hardware Stack Summary

### ✅ TIER 1: Arduino for IoT Sensors

```
Device:       Arduino MKR WiFi 1010
Cost:         $40-60 per unit
Processor:    SAMD21 (32-bit ARM Cortex-M0+)
Memory:       32 KB RAM, 256 KB Flash
Connectivity: WiFi 802.11 b/g/n (2.4 GHz)
Power:        3.3V @ 80 mA (30-day battery + solar)
Deployment:   100+ sensors per site

Typical Sensors:
├─ DHT22 (Temp/Humidity) - $3-5
├─ Capacitive Soil Moisture - $5-10
├─ BH1750 (Light) - $2-3
├─ BMP280 (Pressure) - $2-3
├─ MH-Z19 (CO2) - $20-30
└─ pH Meter (Analog) - $15-20

Software Stack:
├─ IDE: Arduino IDE 2.0 or PlatformIO
├─ Language: C/C++ (Arduino flavor)
├─ Libraries:
│  ├─ WiFi.h - WiFi connectivity
│  ├─ PubSubClient.h - MQTT client
│  ├─ ArduinoJson.h - JSON serialization
│  └─ Adafruit_DHT.h - Sensor drivers
├─ Protocol: MQTT (Publish/Subscribe)
├─ Broker: Mosquitto on Raspberry Pi (192.168.1.100:1883)
└─ Frequency: Publish every 30 seconds

✅ Use Case: Environmental monitoring, sensor telemetry
✅ Advantages: Low power, low cost, easy to deploy
✅ Limitations: Limited processing, WiFi only (no LoRaWAN by default)
```

**Example Arduino Sketch:**
```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
DHT dht(DHT_PIN, DHT22);

void setup() {
  dht.begin();
  WiFi.begin(SSID, PASSWORD);
  mqttClient.setServer(MQTT_BROKER, 1883);
}

void loop() {
  float temp = dht.readTemperature();
  DynamicJsonDocument doc(256);
  doc["device_id"] = "SENSOR_01";
  doc["temperature"] = temp;
  
  char buffer[256];
  serializeJson(doc, buffer);
  mqttClient.publish("sensors/greenhouse/data", buffer);
  
  delay(30000);  // Every 30 seconds
}
```

---

### ✅ TIER 2: ROS 2 Humble for Autonomous Robots

```
Base Platform:  Jetson Xavier NX or Raspberry Pi 4 + Jetson
Cost:           $1500-3000 per robot (DIY)
Processor:      8-core ARM Cortex-A57 (Jetson NX)
Memory:         8-16 GB RAM
Storage:        256 GB NVMe SSD
Connectivity:   WiFi 6 (802.11ax) + Ethernet + 4G
Power:          24V LiPo battery (8S), 4-6 hour operations
Deployment:     10-100 robots per fleet

Sensors:
├─ RPLIDAR A2M8 ($100) - 360° 2D scanning
├─ RealSense D435i ($180) - RGB-D depth camera
├─ BNO055 ($20-30) - IMU (accelerometer, gyro, compass)
├─ Wheel Encoders - Motor feedback
└─ Optional: FLIR thermal camera ($500+)

Actuators:
├─ 12V DC Motors with encoders - Wheel drive
├─ L298N Motor Driver - PWM speed control
├─ 12V Solenoid Pump - Spray system
└─ Servo Motor - Gripper actuation

Software Stack:
├─ OS: Ubuntu 22.04 LTS (arm64)
├─ ROS 2: Humble (LTS until May 2027)
├─ Build System: colcon
├─ Language: Python 3.10 + C++17
├─ Key Packages:
│  ├─ nav2 - Navigation & SLAM
│  ├─ ros2_control - Motor control framework
│  ├─ tf2 - Transform library (coordinate frames)
│  ├─ sensor_msgs - Standard sensor types
│  ├─ geometry_msgs - Pose, velocity, transforms
│  └─ custom_interfaces - Project-specific messages
├─ Middleware: DDS (Fast-RTPS)
├─ Communication: ROS 2 pub/sub, services, actions
└─ Frequency: 10 Hz control loop (0.1 s cycle time)

✅ Use Case: Autonomous field operations, navigation, spray/plant/inspect
✅ Advantages: Full robot OS, mature ecosystem, real-time control
✅ Limitations: Higher power consumption, requires Linux expertise

Node Architecture:
├─ motor_controller_node - Reads /cmd_vel, drives wheels
├─ sensor_fusion_node - Fuses LiDAR + IMU + encoders
├─ nav2_bringup - Navigation stack (SLAM, path planning)
├─ aegis_bridge_node - REST/gRPC ↔ ROS 2 conversion
└─ task_executor_node - Receives Aegis tasks, executes operations
```

**Example ROS 2 Node (Task Executor):**
```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import requests

class TaskExecutor(Node):
    def __init__(self):
        super().__init__('task_executor')
        
        # Create action server for tasks
        self._action_server = ActionServer(...)
        
        # Publish motor commands
        self.cmd_vel_pub = self.create_publisher(
            Twist, '/cmd_vel', 10
        )
        
        # Subscribe to task requests
        self.task_sub = self.create_subscription(
            RoboticTask, '/aegis/task', 
            self.task_callback, 10
        )
    
    def task_callback(self, msg):
        if msg.operation == "SPRAY":
            self.execute_spray(msg)
        elif msg.operation == "NAVIGATE":
            self.execute_navigate(msg)

def main():
    rclpy.init()
    rclpy.spin(TaskExecutor())
```

---

### ✅ TIER 3: Commercial Drone SDK Integration

```
Drone Platform:     DJI Matrice 300 RTK (primary) or Freefly Astro
Cost:               $15,000-25,000 per drone + insurance
Aircraft:           Quad rotor, IP45 rated
Max Flight Time:    45 minutes (45 min/battery)
Payload Capacity:   2.7 kg
Max Distance:       15 km (with range extender)
Max Speed:          19 m/s (68 km/h)
GPS Accuracy:       2 cm (RTK), 5 m (standard)
Operating Altitude: Up to 7000 m MSL

Payload Options:
├─ Zenmuse P1 - 45MP full-frame camera ($5000+)
├─ RTK Module - 2 cm accuracy for surveying
├─ Thermal Camera - Temperature mapping
├─ Multispectral Camera - Crop health index
└─ LIDAR Scanner - 3D terrain mapping

Software Stack:
├─ SDK: DJI PSDK (Payload SDK) or DJI SDK
├─ Language: Python 3.8+ (preferred)
├─ API: RESTful + WebSocket
├─ Libraries:
│  ├─ dji-sdk-python - DJI API wrapper
│  ├─ opencv-python - Image processing
│  ├─ pillow - Image manipulation
│  └─ requests - HTTP requests
├─ Simulator: DJI FlightSimulator (for testing)
├─ Connectivity: OcuSync Enterprise (WiFi 6)
└─ Range: 2-15 km depending on antenna

Communication:
├─ Uplink: Commands, waypoints, mission parameters
├─ Downlink: Real-time video (720p), telemetry, photos
├─ Frequency: 10 Hz telemetry updates
├─ Latency: 100-500 ms typical

✅ Use Case: Aerial surveys, crop health monitoring, RTK mapping
✅ Advantages: RTK positioning, professional-grade cameras, proven platform
✅ Limitations: High cost, requires FAA waiver (Part 107), weather dependent

Example Integration:
1. Create waypoint mission in Python
2. Upload mission to drone via SDK
3. Launch mission (fully autonomous)
4. Receive real-time telemetry
5. Download high-res photos
6. Process photos with Vryndara AI
7. Store results in Aegis database
```

**Example Drone Mission:**
```python
class DroneIntegration:
    def __init__(self):
        self.dji = dji_sdk.DJIFleet()
        self.jwt_token = authenticate_aegis()
    
    def execute_survey(self, task):
        # Create mission
        mission = {
            "waypoints": task["waypoints"],
            "altitude": 100,  # meters
            "speed": 5,       # m/s
            "camera": {"interval": 2, "mode": "PHOTO"}
        }
        
        # Upload and start
        self.dji.upload_mission(mission)
        self.dji.start_mission()
        
        # Wait for completion
        while not self.dji.is_mission_complete():
            time.sleep(5)
        
        # Process photos with AI
        photos = self.dji.download_photos()
        vryndara_results = analyze_with_vryndara(photos)
        
        # Store in Aegis
        save_to_aegis(task["task_id"], vryndara_results)
```

---

## Communication Stack

### Protocol Selection Matrix

```
┌─────────────────────────────────────────────────────────────┐
│            Communication Protocol Recommendations            │
└─────────────────────────────────────────────────────────────┘

Arduino Sensor → MQTT Broker
├─ Protocol: MQTT (Mosquitto)
├─ Port: 1883 (insecure), 8883 (secure)
├─ QoS: 1 (at-least-once delivery)
├─ Topic Format: sensors/{device_id}/{metric}
├─ Frequency: Every 30 seconds
├─ Bandwidth: < 1 Mbps
├─ Latency: 100-500 ms
└─ Power: Low (WiFi minimal)

ROS 2 Robot → Aegis Backend
├─ Protocol: gRPC (HTTP/2)
├─ Port: 50052 (RoboticsService)
├─ Multiplexing: Multiple requests per connection
├─ Message Format: Protocol Buffers
├─ Frequency: Every 5 seconds (status)
├─ Bandwidth: 10-100 Mbps
├─ Latency: 50-200 ms
└─ Power: Medium (continuous WiFi)

Drone → Aegis Backend
├─ Protocol: WebSocket + Manufacturer SDK
├─ Port: 8080-8443 (manufacturer dependent)
├─ Frequency: Real-time (10 Hz telemetry)
├─ Bandwidth: 1-10 Mbps
├─ Latency: 200-1000 ms
└─ Power: Powered (no constraints)
```

---

## Network Infrastructure

```
WiFi Access Points (Ubiquiti UniFi)
├─ 5 GHz Band: For ROS 2 robots (high throughput)
│  ├─ Channel Width: 80 MHz
│  ├─ Data Rate: 433 Mbps
│  ├─ Coverage: ~50m radius
│  └─ Devices: 10-50 robots per AP
├─ 2.4 GHz Band: For Arduino sensors (range priority)
│  ├─ Channel Width: 20 MHz
│  ├─ Data Rate: 72 Mbps
│  ├─ Coverage: ~100m radius
│  └─ Devices: 100+ sensors per AP
└─ Uplink: Gigabit Ethernet backhaul

Edge Gateway (Raspberry Pi 4)
├─ Hardware: 8 GB RAM, 256 GB SSD
├─ Services:
│  ├─ MQTT Broker (Mosquitto) - Port 1883
│  ├─ WiFi AP controller (hostapd)
│  ├─ Sensor aggregator (Python)
│  └─ Local logging & backup
├─ Connectivity: Gigabit Ethernet + 4G LTE backup
└─ Location: Central field location

Cloud Backend (AWS/GCP/On-Prem)
├─ FastAPI Server (Port 8001)
├─ PostgreSQL Database (Port 5432)
├─ Redis Cache (Port 6379)
├─ gRPC Services (Ports 50051, 50052)
└─ Connectivity: 1 Gbps minimum, VPN tunnel from gateway
```

---

## Scalability Matrix

| Component | Single Instance | 100 Robots | 1000 Robots | 10K Robots |
|-----------|-----------------|-----------|------------|-----------|
| Arduino Sensors | 100 | 1,000 | 10,000 | 100,000 |
| ROS 2 Robots | 10 | 100 | 1,000 | 10,000 |
| MQTT Brokers | 1 | 2-5 | 10+ | 50+ |
| Aegis Backends | 1 | 2-3 | 5-10 | 20+ |
| gRPC Servers | 1 | 2 | 5 | 20+ |
| Database | SQLite | PostgreSQL | PostgreSQL HA | Distributed DB |

---

## Implementation Roadmap

```
WEEK 1: Single Arduino Sensor
├─ Hardware setup (Arduino + DHT22)
├─ WiFi connection
├─ MQTT publish
└─ Verify in Aegis dashboard

WEEK 2-3: Multi-Sensor Network
├─ Deploy 5 Arduino nodes
├─ Configure MQTT topics
├─ Implement sensor fusion
└─ Create visualization

WEEK 4-6: ROS 2 Robot
├─ Assemble robot hardware
├─ Install ROS 2 Humble
├─ Implement motor control
├─ Test navigation & obstacle avoidance

WEEK 7-8: Drone Integration
├─ DJI Matrice 300 setup
├─ Mission planning (waypoints)
├─ Photo capture & download
└─ Vryndara image analysis

WEEK 9-12: Multi-Robot Coordination
├─ Deploy 3-5 robots
├─ Test concurrent operations
├─ Implement failover logic
└─ Performance optimization

WEEK 13+: Production Deployment
├─ Scale to 10+ robots
├─ Deploy fleet management dashboard
├─ Setup monitoring & alerting
└─ Document operational procedures
```

---

## Key APIs & Endpoints

```
IoT Sensor Registration:
  POST /api/v1/sensors
  {
    "name": "greenhouse_temp_01",
    "type": "temperature",
    "zone_id": 1,
    "location": "north_wing"
  }

Sensor Data Ingestion:
  POST /api/v1/sensors/data
  {
    "sensor_id": 42,
    "value": 22.5,
    "unit": "°C",
    "timestamp": "2025-05-09T14:30:00Z"
  }

Robot Registration:
  POST /api/v1/robotics/register
  {
    "robot_id": "ROVER_001",
    "robot_type": "AEGIS_ROVER",
    "firmware_version": "2.1.0",
    "capabilities": ["SPRAY", "NAVIGATE", "PLANT"]
  }

Task Dispatch:
  POST /api/v1/robotics/tasks
  {
    "robot_id": "ROVER_001",
    "operation_type": "SPRAY",
    "priority": "HIGH",
    "task_detail": {"zone_id": 3, "volume": 50}
  }

Get Robot Status:
  GET /api/v1/robotics/active
  → Returns: [{robot_id, status, battery, position}, ...]

Mission Report:
  GET /api/v1/research/{task_id}
  → Returns: Vryndara AI analysis results
```

---

## Troubleshooting Quick Reference

| Issue | Cause | Solution |
|-------|-------|----------|
| Arduino WiFi won't connect | Wrong SSID/password | Verify credentials, check 2.4GHz band |
| MQTT publish failing | Broker unreachable | Verify broker IP, check firewall |
| Robot loses connection | Signal too weak | Increase TX power, add WiFi extender |
| gRPC timeout | Network latency | Check 5GHz WiFi signal, reduce payload |
| Drone GPS not converging | Not enough satellites | Move to open sky, wait 60+ seconds |
| Task execution slow | Motor tuning | Adjust PID constants, check encoder feedback |
| Sensor data noisy | Analog interference | Add capacitors, shield cables |
| Dashboard lag | Database query slow | Add indexes, implement caching |

---

## Project References

- **IoT Integration Guide:** `/AEGIS_IOT_INTEGRATION_GUIDE.md`
- **System Architecture:** `/SYSTEM_ARCHITECTURE.md`
- **Diagrams:** `/diagrams/` (6 comprehensive system diagrams)
- **API Docs:** `http://localhost:8001/docs` (when running)
- **ROS 2 Humble:** https://docs.ros.org/en/humble
- **DJI SDK:** https://developer.dji.com/doc

---

**Status:** ✅ Production Ready  
**Last Updated:** May 9, 2026  
**Next Review:** August 9, 2026

