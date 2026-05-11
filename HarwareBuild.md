To showcase the "full potential" of Aegis on a student budget, you don't need a 100-acre farm; you need a **functional ecosystem model**. For your 7th-semester showcase, we will focus on building **four distinct hardware categories** that prove the Vryndara kernel can manage different classes of "agents" simultaneously.

Here is the "Zero-Budget" bill of materials and implementation guide.

---

## 1. The Aegis "Overseer" Rover (1 Unit)

This is your flagship. It proves heavy-duty navigation and security.

* **Function:** Perimeter security and macro-monitoring.
* **Build Method:** Use **PVC Pipes (1-inch)** for the chassis. It’s cheaper and stronger than wood.
* **Parts & Cost:**
* **Brain:** ESP32-WROOM (₹350).
* **Vision:** ESP32-CAM (₹450) – provides a live RTSP feed to Vryndara.
* **Drive:** 4x Geared DC Motors (₹400) + L298N Motor Driver (₹150).
* **Power:** 3x 18650 Cells (Salvage from an old laptop battery - ₹0).


* **Total Cost:** **~₹1,350**

## 2. Agri-Swarm "Micro-Bot" (1 Unit)

This proves the "swarm" logic for precision tasks like weeding or planting.

* **Function:** Navigate tight spaces where the Rover cannot go.
* **Build Method:** **Sunboard/Foam-sheet** chassis (₹50). Use a simple 2-wheel + castor design.
* **Parts & Cost:**
* **Brain:** ESP32 (₹350).
* **Actuator:** 1x SG90 Mini Servo (₹120) – to simulate a "planting arm."
* **Drive:** 2x Small BO Motors + Wheels (₹180).


* **Total Cost:** **~₹700**

## 3. IoT "Mycelial" Mesh Probes (3 Units)

These prove the offline biological monitoring capabilities of Vryndara.

* **Function:** Soil moisture and "Acoustic Pest" monitoring.
* **Build Method:** Use **PVC End-caps** or small plastic bottles as waterproof housings.
* **Parts & Cost (per unit):**
* **Brain:** ESP32 (₹350).
* **Sensing:** Capacitive Soil Moisture Sensor (₹120) + Sound Sensor/Mic (₹80).


* **Total Cost:** **₹550 per unit (Total ₹1,650)**

## 4. The Master Vault Prototype (1 Unit)

This proves the "Seed Godown" climate-control logic.

* **Function:** Monitor and maintain the -18°C seed storage simulation.
* **Build Method:** A small **Styrofoam/Thermocol box** (salvage from a medicine or fish box).
* **Parts & Cost:**
* **Brain:** ESP32 (₹350).
* **Environment:** DHT11 Temp/Humidity Sensor (₹100).
* **Cooling Sim:** A small 5V CPU Fan (Salvage from old PC - ₹0).


* **Total Cost:** **~₹450**

---

### Total Hardware Investment: ~₹4,150

*This covers the full ecosystem: 1 Rover, 1 Micro-bot, 3 Mesh Probes, and 1 Vault.*

---

## The Connection Logic: Vryndara gRPC Kernel

To showcase the "full potential," your connection architecture must be strictly local and high-speed.

1. **The Base Station:** Your laptop runs the **Vryndara Kernel** (Python/gRPC server).
2. **The Local Network:** Turn on your laptop's **Mobile Hotspot**. All ESP32s connect to this. No internet is required.
3. **Communication Protocol:**
* Every device runs a **gRPC Client** using the `nanopb` library.
* The IoT probes "Push" data (Soil: 40%, Pest: None) to the Kernel.
* The Kernel "Pushes" commands (Rover: Move to Zone B) to the robots.



---

## 7th Semester Showcase Demo Scenario

To make people believe in the Crore-rupee potential, follow this demo flow:

1. **Biological Alert:** Pour dry sand on one IoT Probe. The Vryndara Dashboard immediately shows "Critical Drought in Zone A."
2. **Autonomous Response:** Vryndara triggers a gRPC call. The **Agri-Swarm bot** moves to that probe and lowers its "arm" (servo) to simulate watering.
3. **Security Integration:** Tap the "Acoustic Sensor" on a probe. The Dashboard flags an "Unknown Intruder." The **Aegis Rover** automatically turns its camera toward that zone and streams the video.
4. **Vault Integrity:** Open the Styrofoam box. The temperature rises; the dashboard turns red, and the CPU fan kicks in to "stabilize" the environment.

### Final Checklist for Next Semester:

* **Procurement:** Buy ESP32s first. They are the most versatile part.
* **Salvage:** Start collecting old laptop batteries (for 18650 cells) and old printers (for motors/gears).
* **Simulation:** Use **Wokwi** (Online ESP32 Simulator) to write your gRPC code *before* the hardware arrives to save time.

Since you are handling the hardware integration yourself, do you have access to a basic soldering iron and a multi-meter in your college lab?