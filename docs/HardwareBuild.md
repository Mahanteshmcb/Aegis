To showcase the "full potential" of Aegis on a student budget, you don't need a 100-acre farm; you need a **comprehensive ecosystem prototype** that demonstrates all roadmap requirements from Day 1-150. For your 7th-semester showcase, we will build **eight distinct hardware categories** that prove the Vryndara kernel can manage different classes of "agents" simultaneously across an estate-scale deployment.

Here is the "Comprehensive Prototype" bill of materials and implementation guide covering all Phase 2 hardware requirements (Days 71-150).

---

## 1. Aegis "Overseer" Rover Fleet (2 Units)

This proves heavy-duty navigation, security, and estate-wide monitoring.

* **Function:** Perimeter security, macro-monitoring, and payload transport across the estate.
* **Build Method:** Use **PVC Pipes (1-inch)** for the chassis. It's cheaper and stronger than wood.
* **Parts & Cost per Unit:**
* **Brain:** ESP32-WROOM (₹350).
* **Vision:** ESP32-CAM (₹450) – provides RTSP feed to Vryndara.
* **Drive:** 4x Geared DC Motors (₹400) + L298N Motor Driver (₹150).
* **Power:** 3x 18650 Cells (Salvage from old laptop battery - ₹0).
* **Sensors:** Ultrasonic Distance Sensor (₹100) for obstacle avoidance.

* **Total Cost per Unit:** **~₹1,450**
* **Total for 2 Units:** **₹2,900**

## 2. Agri-Swarm "Micro-Bot" Fleet (4 Units)

This proves the "swarm" logic for precision tasks like weeding, planting, and maintenance.

* **Function:** Navigate tight spaces where Rovers cannot go, perform coordinated agricultural tasks.
* **Build Method:** **Sunboard/Foam-sheet** chassis (₹50). Use 2-wheel + castor design.
* **Parts & Cost per Unit:**
* **Brain:** ESP32 (₹350).
* **Actuator:** 1x SG90 Mini Servo (₹120) – for planting/weeding arm.
* **Drive:** 2x Small BO Motors + Wheels (₹180).
* **Sensors:** IR Proximity Sensor (₹80) for obstacle detection.

* **Total Cost per Unit:** **~₹780**
* **Total for 4 Units:** **₹3,120**

## 3. IoT "Mycelial" Mesh Probes (6 Units)

These prove the offline biological monitoring capabilities of Vryndara across multiple zones.

* **Function:** Soil moisture, pH, temperature monitoring with mesh networking.
* **Build Method:** Use **PVC End-caps** or small plastic bottles as waterproof housings.
* **Parts & Cost per Unit:**
* **Brain:** ESP32 (₹350).
* **Sensing:** Capacitive Soil Moisture Sensor (₹120) + DHT11 Temp/Humidity (₹100) + pH Sensor (₹150).
* **Communication:** LoRa Module (₹200) for mesh networking.

* **Total Cost per Unit:** **~₹920**
* **Total for 6 Units:** **₹5,520**

## 4. Acoustic Pest Detection Sensors (4 Units)

This proves the ML-powered pest recognition from the roadmap (Day 38).

* **Function:** Real-time acoustic monitoring for insect detection and classification.
* **Build Method:** **Plastic enclosures** with weatherproofing.
* **Parts & Cost per Unit:**
* **Brain:** ESP32 (₹350).
* **Audio:** High-sensitivity Microphone Module (₹200) + Audio Amplifier (₹100).
* **Power:** Solar Panel (2W) + LiPo Battery (₹150).

* **Total Cost per Unit:** **~₹800**
* **Total for 4 Units:** **₹3,200**

## 5. Master Vault Climate Control (2 Units)

This proves the "Seed Godown" climate-control logic for storage facilities.

* **Function:** Monitor and maintain optimal storage conditions for seeds and supplies.
* **Build Method:** **Styrofoam/Thermocol boxes** (salvage from medicine boxes).
* **Parts & Cost per Unit:**
* **Brain:** ESP32 (₹350).
* **Environment:** DHT11 Temp/Humidity Sensor (₹100) + DS18B20 Waterproof Temp (₹120).
* **Cooling:** 5V CPU Fan (Salvage - ₹0) + Peltier Cooler (₹200).
* **Power:** 18650 Battery Pack (₹100).

* **Total Cost per Unit:** **~₹770**
* **Total for 2 Units:** **₹1,540**

## 6. Canopy Drone Prototypes (2 Units)

This proves vertical operations and aerial monitoring (Day 80).

* **Function:** Upper canopy monitoring and soft manipulation tasks.
* **Build Method:** **Lightweight foam frame** with tethered operation for safety.
* **Parts & Cost per Unit:**
* **Brain:** ESP32 (₹350).
* **Flight:** Quadcopter Frame Kit (₹500) + 4x Coreless Motors (₹300).
* **Control:** Flight Controller (₹400) + IMU Sensor (₹150).
* **Vision:** Camera Module (₹200).

* **Total Cost per Unit:** **~₹1,900**
* **Total for 2 Units:** **₹3,800**

## 7. Estate Infrastructure Sensors (8 Units)

This proves living quarters, laboratory, and facility monitoring (Days 85-91).

* **Function:** Environmental control and safety monitoring across estate buildings.
* **Build Method:** **Wall-mount enclosures** with standard electronics mounting.
* **Parts & Cost per Unit:**
* **Brain:** ESP32 (₹350).
* **Sensing:** MQ-135 Air Quality (₹150) + PIR Motion (₹80) + Light Sensor (₹50).
* **Actuator:** Relay Module for lights/fans (₹100).

* **Total Cost per Unit:** **~₹730**
* **Total for 8 Units:** **₹5,840**

## 8. Energy & Water Management Nodes (4 Units)

This proves estate-wide energy optimization and water recycling (Days 89, 91).

* **Function:** Monitor and control power distribution and water systems.
* **Build Method:** **Weatherproof outdoor enclosures**.
* **Parts & Cost per Unit:**
* **Brain:** ESP32 (₹350).
* **Energy:** Current Sensor (₹120) + Voltage Sensor (₹100).
* **Water:** Flow Sensor (₹150) + Water Level Sensor (₹100).
* **Power:** Solar Charge Controller (₹200).

* **Total Cost per Unit:** **~₹1,020**
* **Total for 4 Units:** **₹4,080**

---

### Final Procurement List - All Items Required

| Item | Quantity | For Device | Unit Cost (₹) | Total Cost (₹) |
|------|----------|------------|---------------|----------------|
| ESP32-WROOM | 2 | Overseer Rovers | 350 | 700 |
| ESP32-CAM | 2 | Overseer Rovers | 450 | 900 |
| ESP32 | 26 | All other devices | 350 | 9,100 |
| Geared DC Motors (4x) | 2 | Overseer Rovers | 400 | 800 |
| L298N Motor Driver | 2 | Overseer Rovers | 150 | 300 |
| Ultrasonic Sensor | 2 | Overseer Rovers | 100 | 200 |
| SG90 Mini Servo | 4 | Micro-Bots | 120 | 480 |
| BO Motors + Wheels (2x) | 4 | Micro-Bots | 180 | 720 |
| IR Proximity Sensor | 4 | Micro-Bots | 80 | 320 |
| Capacitive Soil Moisture | 6 | Mycelial Probes | 120 | 720 |
| DHT11 Temp/Humidity | 8 | Probes + Vaults | 100 | 800 |
| pH Sensor | 6 | Mycelial Probes | 150 | 900 |
| LoRa Module | 6 | Mycelial Probes | 200 | 1,200 |
| Microphone Module | 4 | Acoustic Sensors | 200 | 800 |
| Audio Amplifier | 4 | Acoustic Sensors | 100 | 400 |
| Solar Panel (2W) | 4 | Acoustic Sensors | 150 | 600 |
| LiPo Battery | 4 | Acoustic Sensors | 150 | 600 |
| DS18B20 Waterproof Temp | 2 | Vaults | 120 | 240 |
| Peltier Cooler | 2 | Vaults | 200 | 400 |
| Quadcopter Frame Kit | 2 | Drones | 500 | 1,000 |
| Coreless Motors (4x) | 2 | Drones | 300 | 600 |
| Flight Controller | 2 | Drones | 400 | 800 |
| IMU Sensor | 2 | Drones | 150 | 300 |
| Camera Module | 2 | Drones | 200 | 400 |
| MQ-135 Air Quality | 8 | Infrastructure | 150 | 1,200 |
| PIR Motion Sensor | 8 | Infrastructure | 80 | 640 |
| Light Sensor | 8 | Infrastructure | 50 | 400 |
| Relay Module | 8 | Infrastructure | 100 | 800 |
| Current Sensor | 4 | Energy Nodes | 120 | 480 |
| Voltage Sensor | 4 | Energy Nodes | 100 | 400 |
| Flow Sensor | 4 | Energy Nodes | 150 | 600 |
| Water Level Sensor | 4 | Energy Nodes | 100 | 400 |
| Solar Charge Controller | 4 | Energy Nodes | 200 | 800 |
| PVC Pipes (1-inch, 2m) | 4 | Rovers | 100 | 400 |
| Sunboard/Foam-sheet (A4) | 8 | Micro-Bots | 50 | 400 |
| PVC End-caps | 12 | Probes | 20 | 240 |
| Plastic Enclosures | 16 | Various | 50 | 800 |
| Styrofoam Boxes | 4 | Vaults | 50 | 200 |
| Foam Frame | 4 | Drones | 100 | 400 |
| Wall-mount Enclosures | 8 | Infrastructure | 80 | 640 |
| Weatherproof Boxes | 4 | Energy Nodes | 150 | 600 |
| 18650 Cells (3x per pack) | 6 | Rovers + Vaults | 0 (salvage) | 0 |
| CPU Fans (5V) | 2 | Vaults | 0 (salvage) | 0 |

### Total Hardware Investment: ~₹47,000 (INR)

*This covers a comprehensive prototype estate with: 2 Rovers, 4 Micro-Bots, 6 Mycelial Probes, 4 Acoustic Sensors, 2 Vaults, 2 Drones, 8 Infrastructure Sensors, 4 Energy Nodes - representing all hardware categories from Days 71-150.*

*Note: Costs are approximate for Indian market as of 2026. Bulk purchasing from Robu.in, Amazon India, or local electronics markets can reduce costs by 20-30%. Salvage items (batteries, fans) bring effective cost down significantly. All components are student-budget friendly and demonstrate full estate-scale capabilities.*

---

## Integration with Aegis Software Stack

Your hardware prototypes directly integrate with the existing Aegis codebase:

* **Backend Integration:** Sensor data flows via MQTT → FastAPI backend → SQLite database. Use the `/api/v1/sensors` endpoints for data ingestion.
* **AI Orchestration:** The Vryndara kernel (in `ai/` folder) processes sensor data and generates autonomous responses.
* **Frontend Visualization:** Real-time data appears on the Next.js dashboard (`frontend/pages/sensors.js`).
* **Blockchain Audit:** All sensor readings and actuator commands are logged to the Ethereum audit trail for tamper-proof records.
* **Testing Tools:** Use `python scripts/simulation/simulate_sensors.py` to test the full pipeline before hardware assembly.

This setup proves Aegis can manage real-world IoT deployments while maintaining the decentralized, offline-first architecture.

---

## The Connection Logic: MQTT-Based Local Network

To showcase the "full potential," your connection architecture must be strictly local and reliable.

1. **The Base Station:** Your laptop runs the **Aegis Backend** (FastAPI server) and **MQTT Broker** (Mosquitto).
2. **The Local Network:** Turn on your laptop's **Mobile Hotspot**. All ESP32s connect to this. No internet is required.
3. **Communication Protocol:**
* Every device runs an **MQTT Client** using MicroPython's `umqtt` library.
* The IoT probes "Publish" data (Soil: 40%, Pest: None) to MQTT topics.
* The Backend "Subscribes" to sensor topics and ingests data.
* The Backend "Publishes" commands (Rover: Move to Zone B) to actuator topics.

---

## 7th Semester Showcase Demo Scenario

To make people believe in the Crore-rupee potential, follow this demo flow:

1. **Biological Alert:** Pour dry sand on one IoT Probe. The sensor publishes low moisture data via MQTT. The Aegis Backend ingests it and triggers a dashboard alert: "Critical Drought in Zone A."
2. **Autonomous Response:** The Vryndara AI kernel analyzes the data and orchestrates a response. It sends commands via the Backend, which publishes MQTT messages. The **Agri-Swarm bot** receives the command and moves to that probe, lowering its "arm" (servo) to simulate watering.
3. **Security Integration:** Tap the "Acoustic Sensor" on a probe. The sensor detects vibration and publishes alert data. The Dashboard flags an "Unknown Intruder." The **Aegis Rover** receives navigation commands via MQTT and turns its camera toward that zone, streaming video via RTSP.
4. **Vault Integrity:** Open the Styrofoam box. The temperature sensor publishes rising temperature data. The dashboard turns red, and the Backend publishes commands to activate the CPU fan to "stabilize" the environment.

### Final Checklist for Next Semester:

* **Procurement:** Buy ESP32s first. They are the most versatile part. Source from local electronics stores or online (Robu.in, Amazon India).
* **Salvage:** Start collecting old laptop batteries (for 18650 cells) and old printers (for motors/gears). Check university e-waste or local repair shops.
* **Software Setup:**
  - Install Mosquitto MQTT broker on your laptop.
  - Flash ESP32 devices with MicroPython and test MQTT connectivity using the provided `iot/esp32_sensor.py` template.
  - Use `python scripts/simulation/simulate_sensors.py` to test backend integration before hardware arrives.
* **Testing:** Calibrate sensors (soil moisture in different soil types, acoustic threshold for pest detection). Ensure all devices connect to your hotspot and publish data to correct MQTT topics.
* **Safety:** Use proper power management to avoid battery fires. Test all circuits before connecting to ESP32.