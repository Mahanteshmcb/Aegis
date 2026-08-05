# Aegis College Prototype Hardware Plan

This file defines a low-cost hardware prototype for the Aegis project suitable for semester testing, demos, and end-to-end verification. The design is constrained to approximately ₹5,000 and will not exceed ₹10,000.

## Prototype Goals

* Validate end-to-end IoT sensor ingestion and backend processing.
* Demonstrate robotics control and actuator response.
* Show real-time dashboard updates for environmental and security data.
* Keep the hardware bill of materials low-cost, student-friendly, and easy to assemble.

---

## 1. Core Prototype Devices

### 1.1. Overseer Rover (1 Unit)

* **Function:** Security and navigation demo.
* **Key capabilities:** Motor control, obstacle detection, camera preview.
* **Parts & cost:**
  * ESP32-WROOM / ESP32 DevKit V1 — ₹350
  * 4x small DC geared motors — ₹200
  * L298N motor driver — ₹150
  * Ultrasonic sensor HC-SR04 — ₹100
  * PVC sheet / acrylic chassis material — ₹100
  * Jumper wires and hardware — ₹100

* **Estimated cost:** ₹1,000

### 1.2. Agri-Swarm Micro-Bot (1 Unit)

* **Function:** Small robot for precision task simulation.
* **Key capabilities:** Servo actuation, movement, zone response.
* **Parts & cost:**
  * ESP32 DevKit V1 — ₹350
  * 2x BO motors + wheels — ₹120
  * SG90 servo — ₹120
  * Castor wheel and chassis board — ₹80
  * Jumper wires — ₹50

* **Estimated cost:** ₹720

### 1.3. IoT Soil & Climate Probe (2 Units)

* **Function:** Environmental monitoring for moisture and temperature.
* **Key capabilities:** Soil moisture sensing, temperature/humidity reporting.
* **Parts & cost per unit:**
  * ESP32 DevKit V1 — ₹350
  * Capacitive soil moisture sensor — ₹120
  * DHT11 sensor — ₹100
  * Small plastic enclosure / bottle — ₹30

* **Estimated cost per unit:** ₹600
* **Total for 2 units:** ₹1,200

### 1.4. Master Vault Monitor (1 Unit)

* **Function:** Storage-condition alert simulation.
* **Key capabilities:** Temperature/humidity tracking and fan control.
* **Parts & cost:**
  * ESP32 DevKit V1 — ₹350
  * DHT11 sensor — ₹100
  * Small 5V fan (salvage or ₹100) — ₹0-100
  * Relay module — ₹80
  * Styrofoam box — ₹50

* **Estimated cost:** ₹580

### 1.5. Acoustic Alert Sensor (1 Unit)

* **Function:** Security/pest trigger demonstration.
* **Key capabilities:** Sound/vibration detection and alert generation.
* **Parts & cost:**
  * ESP32 DevKit V1 — ₹350
  * Sound sensor module — ₹80
  * Plastic enclosure — ₹30

* **Estimated cost:** ₹460

---

## 2. Required Supporting Hardware

* **USB power adapters / chargers** — ₹300
* **Breadboard + jumper wire kit** — ₹250
* **Battery pack or power bank** — ₹400
* **SD card or small shield (optional for logging)** — ₹200
* **Misc hardware (screws, glue, tape)** — ₹150

* **Estimated support cost:** ₹1,300

---

## 3. Total Prototype Cost Estimate

| Item | Quantity | Estimated Cost (₹) |
|------|----------|--------------------|
| Overseer Rover | 1 | 1,000 |
| Agri-Swarm Micro-Bot | 1 | 720 |
| Soil & Climate Probe | 2 | 1,200 |
| Master Vault Monitor | 1 | 580 |
| Acoustic Alert Sensor | 1 | 460 |
| Supporting hardware | - | 1,300 |
| **Total** | - | **₹5,260** |

> This prototype stays within the target of ₹5,000–₹10,000 and remains practical for college-level testing and demo work.

---

## 4. Exact Purchase Order List

### Electronic Modules and Boards
* 6x ESP32 DevKit V1 boards — ₹350 each — **₹2,100**
* 1x ESP32-WROOM / ESP32 DevKit V1 spare — ₹350 — **₹350**
* 1x L298N motor driver module — ₹150 — **₹150**
* 4x small DC geared motors — ₹200 total — **₹200**
* 2x BO motors + wheels sets — ₹120 total — **₹120**
* 1x SG90 micro servo — ₹120 — **₹120**
* 1x HC-SR04 ultrasonic sensor — ₹100 — **₹100**
* 2x DHT11 temperature/humidity sensors — ₹100 each — **₹200**
* 2x capacitive soil moisture sensors — ₹120 each — **₹240**
* 1x sound sensor module — ₹80 — **₹80**
* 1x relay module — ₹80 — **₹80**

### Mechanical and Assembly Materials
* PVC sheet or acrylic sheet for chassis — ₹100 — **₹100**
* Plastic enclosure / bottle for probe housings — ₹60 — **₹60**
* Styrofoam box for Vault Monitor — ₹50 — **₹50**
* Castor wheel and chassis board for Micro-Bot — ₹80 — **₹80**
* Jumper wires and small hardware pack — ₹100 — **₹100**

### Power and Support Hardware
* USB power adapters / chargers — ₹300 — **₹300**
* Breadboard + jumper wire kit — ₹250 — **₹250**
* Battery pack or power bank — ₹400 — **₹400**
* Optional SD card / small shield for logging — ₹200 — **₹200**
* Misc screws, glue, tape, zip ties — ₹150 — **₹150**

### Total Purchase Cost
* **Total hardware order cost:** ₹5,260

> Order all items together to keep the build simple and stay within the ₹5,000-₹10,000 budget.

---

## 5. Device-to-Requirement Mapping

* **ESP32 boards**: Core compute for all devices and a direct match to your existing IoT stack.
* **Motor driver + motors**: Demonstrates robotic motion control and backend actuator dispatch.
* **Ultrasonic sensor**: Validates perimeter/obstacle detection for the Rover.
* **Soil moisture + DHT11**: Covers environmental monitoring, irrigation, and climate conditions.
* **Relay + fan**: Simulates vault climate control and emergency response.
* **Sound sensor**: Captures acoustic alert requirements for security/pest detection.

---

## 6. Recommended Prototype Architecture

1. **Network:** Laptop hosts FastAPI backend and Mosquitto MQTT broker.
2. **Edge:** ESP32 units connect over local WiFi hotspot.
3. **Protocol:** MQTT for telemetry and control.
4. **Dashboard:** Frontend fetches sensor status and command state from backend.
5. **Validation:** Use `simulate_sensors.py` for backend validation before hardware is assembled.

---

## 7. Buying Strategy

* Prioritize sourcing **ESP32 DevKit V1** and **sensors** from local electronics markets to avoid shipping delays.
* Salvage power modules and fans from old PC/laptops to reduce cost.
* Keep the first purchase focused on 1 prototype of each category, not multiple fleet units.
* After the first working prototype, expand to extra units if budget allows.

---

## 8. Notes for Next Semester Prototype Expansion

If budget allows later, add:
* A second Rover or Micro-Bot
* More soil probes (up to 4 total)
* LoRa for longer-range mesh networking
* ESP32-CAM for live video
* Battery management modules (TP4056, boost converters)

This roadmap gives you a strong college prototype for around ₹5,260 while preserving the core Aegis story and demo capability.