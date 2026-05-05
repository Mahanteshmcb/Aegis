# 🤖 Project Aegis: Mobile Hardware Repurposing & Headless Node Provisioning

**Objective:** To systematically diagnose, wipe, format, and repurpose a corrupted or hard-bricked Android device into a headless compute node for the Aegis multi-agent security rover. 

Hardware failure is just a rite of passage in hardware hacking and robotics.[cite: 1] The diagnostic process documented here demonstrates how to systematically strip away software barriers until only physical electrical faults remain.[cite: 1] This is the exact mindset needed for building autonomous systems; you must understand *what* the commands are actually doing to the silicon, not just *how* to run them.[cite: 1]

Since we are repurposing old smartphones as headless compute nodes, having a standardized procedure is critical.[cite: 1] This document serves as the official Standard Operating Procedure (SOP) for provisioning future MTK-based nodes.[cite: 1]

---

## 🏗️ 1. Architecture: What is Installed & Where It Lives

When provisioning a mobile device from a hard-brick state, operations occur across two distinct environments: the **Host (Your PC)** and the **Target (The Phone)**.[cite: 1]

### 💻 On Your Host PC (The Commander)
The host PC dictates the commands and bypasses the device's security.
*   **Python & mtkclient:** This is your command center.[cite: 1] `mtkclient` is a reverse-engineering exploit framework.[cite: 1] It does not "install" on the phone; it lives locally (e.g., `C:\Aegis\mtkclient...`) and pushes temporary instructions into the phone's RAM via USB.[cite: 1]
*   **MediaTek VCOM Drivers:** Installed deep in Windows.[cite: 1] These tell your laptop how to interpret the raw electrical signals coming from the phone's BootROM before an operating system exists.[cite: 1]
*   **The Kamakiri Payload:** This is a microscopic exploit included in `mtkclient`.[cite: 1] When you connect the phone, `mtkclient` injects this payload into the phone's CPU to disable its hardware security (SLA/DAA), giving you root-level read/write access to the flash storage.[cite: 1]

### 📱 On the Target Phone (The Node)
You do not conventionally "install" software here; you inject raw binary data into specific physical addresses on the **UFS (Universal Flash Storage)** chip.[cite: 1]
*   **`preloader` (Sector 0):** This is the very first piece of code the CPU reads when it gets power.[cite: 1] It initializes the RAM and USB.[cite: 1] It lives in a hidden hardware boot partition (LU0/LU1), not a standard Android partition.[cite: 1]
*   **`lk` (Little Kernel / Bootloader):** The traffic cop.[cite: 1] It initializes the screen, the battery charging logic, and Fastboot mode.[cite: 1]
*   **`boot` (The Kernel):** The bridge.[cite: 1] This contains the hardware drivers (camera, wifi, CPU governors) that allow the Android software to talk to the physical motherboard.[cite: 1]
*   **`vbmeta` (Verified Boot):** The cryptographic lock.[cite: 1] It holds the digital signatures that tell the phone, "Yes, this boot image is safe to load."[cite: 1]
*   **`super` (The OS):** A massive partition containing the actual Android interface, system apps, and frameworks.[cite: 1]

---

## 🔌 2. The Hardware Reality: Power, Pins, and PMIC

When stripping a mobile device down, hardware electrical loops often mask themselves as software bootloops. The **Power Management IC (PMIC)** is the gatekeeper. 

*   **The USB vs. Battery Gap:** A standard laptop USB port provides $5V$ at roughly $500mA$ to $900mA$. This is enough to power the BootROM (BROM) and accept flash commands. However, transitioning from the Preloader to the Android Kernel causes a massive current spike as the CPU, RAM, and GPU initialize.
*   **The FPC Failure:** If the battery's Flexible Printed Circuit (FPC) connector on the motherboard is broken, the phone loses its power buffer. When the kernel demands current, the USB voltage drops, the PMIC detects an under-voltage or open-circuit error, and the CPU resets.
*   **Diagnostic Indicator:** If a device successfully flashes via `mtkclient` but constantly reconnects/disconnects in Device Manager without vibrating, it is suffering from a hardware-level power gap, not a corrupted bootloader. 

---

## 🛠️ 3. Cross-Platform Adaptation (The Chipset Rule)

The single most important rule in mobile hardware hacking: **The tools change based on the CPU manufacturer, not the phone brand.**[cite: 1]

### 🟦 If the device is MediaTek (MTK)
*   **The Tool:** You will use `mtkclient` or SP Flash Tool.[cite: 1]
*   **The Handshake:** Volume Up + Volume Down (BROM Mode).[cite: 1]
*   **The Files:** You must source the exact `preloader.bin` and scatter file for that specific processor (e.g., Helio G96, Dimensity 9000).[cite: 1] A mismatched preloader will hard-brick the device instantly.[cite: 1]

### 🟥 If the device is Snapdragon (Qualcomm)
*   **The Tool:** `mtkclient` is useless here.[cite: 1] You will use **QFIL** (Qualcomm Flash Image Loader) or MiFlash.[cite: 1]
*   **The Handshake:** You must trigger **EDL Mode (Emergency Download Mode)**.[cite: 1] This is often done via ADB (`adb reboot edl`), a specialized deep-flash USB cable, or by physically opening the phone and shorting two specific "Test Point" pins on the motherboard with metal tweezers.[cite: 1]
*   **The Files:** Instead of a `preloader.bin`, you need a **Firehose file** (`.mbn`).[cite: 1] This file acts as the secure key to unlock the Qualcomm storage.[cite: 1]

### 🟩 If the device is Unisoc (Spreadtrum)
*   **The Tool:** SPD Research Download Tool.[cite: 1]
*   **The Files:** Packed into a single `.pac` file instead of individual `.img` files.[cite: 1]

---

## 📋 4. The Aegis Node Pre-Flight Checklist

Before you attempt to flash, root, or wipe *any* future mobile device for your robotics cluster, run through this checklist to prevent the hardware and software loops you just fought through.[cite: 1]

### Hardware Checks
*   **Battery Integrity:** Verify the internal battery is physically connected and holding above 3.8V.[cite: 1] A dead or disconnected battery will cause voltage-drop resets the moment the CPU tries to exit low-power mode.[cite: 1]
*   **Button Functionality:** Ensure the Volume buttons physically "click" and register.[cite: 1] If a volume button is broken, you cannot manually trigger BROM or Fastboot mode in an emergency.[cite: 1]
*   **Data Cable:** Use a USB 3.0 or high-quality data cable.[cite: 1] Cheap charging-only cables will provide power but fail the data handshake.[cite: 1]

### Software Checks
*   **Verify the SOC (System on Chip):** Do not trust the phone's marketing name.[cite: 1] Google the exact model number (e.g., "Infinix X698 CPU") to confirm if it is MTK, Snapdragon, or Unisoc.[cite: 1]
*   **Match the Firmware:** Download the stock ROM that exactly matches the device's original region and hardware version.[cite: 1] Flashing an Indian ROM on a Global device can cause cellular modem failures.[cite: 1]
*   **Locate the "Get Out of Jail" Files:** Before formatting anything, ensure you have the `boot.img`, `vbmeta.img`, and `preloader` / `firehose` files extracted and ready on your PC.[cite: 1]
*   **Driver Verification:** Open Windows Device Manager *before* you start.[cite: 1] Plug the phone in while holding the boot keys.[cite: 1] Verify that a specific chipset port appears (e.g., `MediaTek USB Port` or `Qualcomm HS-USB QDLoader 9008`) and does not have a yellow warning triangle.[cite: 1]

---

## 🚀 5. Aegis Node Provisioning Protocol: MediaTek Architecture

**Objective:** To completely format a corrupted or locked MediaTek Android device, bypass hardware-level bootloops, and establish a headless ADB connection for multi-agent AI deployment.[cite: 1]

**Prerequisites:**[cite: 1]
*   A host PC with Python installed.[cite: 1]
*   The `mtkclient` repository and MediaTek USB VCOM drivers.[cite: 1]
*   The stock firmware for the specific device (containing `boot.img`, `vbmeta.img`, `lk.img`, and the `preloader.bin`).[cite: 1]

### Phase 1: The "Clean Slate" Wipe
Before flashing new data, you must destroy the old partition structures and any ghost instructions (like kernel panic loops stored in the `misc` partition).[cite: 1]

**The Command:**[cite: 1]
```cmd
python mtk.py e metadata,userdata,cache,misc,para --preloader <your_preloader.bin>
```
**How to Execute:**[cite: 1]
1. Unplug the phone and disconnect the battery (if possible) for 10 seconds.[cite: 1]
2. Hit Enter on the PC terminal.[cite: 1]
3. Hold **Volume Up + Volume Down**, plug in the USB, and snap the battery in immediately when the terminal detects the port.[cite: 1]

**Expected Output:**[cite: 1]
```text
DAXFlash - Formatting addr 0xeda2000 with length 0x2000000, please standby....
Done |██████████| 100.0% Erasing: (0x2000000/0x2000000),0.00 MB/s
DAXFlash - Successsfully formatted addr...
All partitions formatted.
```

### Phase 2: The Core Synchronization (Boot & Security)
Modern Android devices use an A/B partition structure and a "Chain of Trust."[cite: 1] The Kernel (`boot`) and the Security Gatekeeper (`vbmeta`) must match perfectly on both slots, otherwise the Preloader will trigger a Watchdog Reset (vibration loop).[cite: 1]

**The Command:**[cite: 1]
```cmd
python mtk.py w boot_a,boot_b,vbmeta_a,vbmeta_b boot.img,boot.img,vbmeta.img,vbmeta.img --preloader <your_preloader.bin>
```
**How to Execute:**[cite: 1]
Same BROM handshake as Phase 1 (Hold Vol Up + Vol Down, connect USB).[cite: 1]

**Expected Output:**[cite: 1]
```text
Progress: |██████████| 100.0% Write: (0x2000000/0x2000000), 5.14 MB/s  s left
Wrote boot.img to sector 151552 with sector count 8192.
Done |██████████| 100.0% Write: (0x1000/0x1000),0.00 MB/s
Wrote vbmeta.img to sector 42760 with sector count 2048.
```

### Phase 3: The Bootloader Injection
If the device refuses to show up in Fastboot mode or the screen won't turn on, the Little Kernel (`lk`) and `preloader` are corrupted.[cite: 1] Because the preloader lives outside standard partitions on UFS storage, it requires a special force-write command.[cite: 1]

**The Commands (Run Sequentially):**[cite: 1]
```cmd
python mtk.py w lk_a,lk_b lk.img,lk.img --preloader <your_preloader.bin>
python mtk.py wf <your_preloader.bin>
```

**Expected Output:**[cite: 1]
```text
Done |██████████| 100.0% Write: (0x127800/0x127800),0.00 MB/s
Wrote lk.img to sector 148992 with sector count 512.
Done |██████████| 100.0% Write: (0x4FA00/0x4FA00),0.00 MB/s
Wrote preloader.bin to sector 0 with sector count 637.
```

### Phase 4: Hardware Security Override
To ensure the hardware doesn't reject your modifications upon the first boot, you must disable the internal security configuration flags.[cite: 1]

**The Command:**[cite: 1]
```cmd
python mtk.py da seccfg unlock --preloader <your_preloader.bin>
```

**Expected Output:**[cite: 1]
```text
Sej - AES128 CBC - HACC run
SecCfgV4 - hwtype found: V4
DaHandler - [LIB]: Device is already unlocked
```

### Phase 5: The Headless ADB Handshake
Once the phone is physically reassembled (with a healthy battery connection) and powered on for a full 10 minutes to rebuild its internal encryption, you can establish the headless display.[cite: 1]

**The Commands:**[cite: 1]
```cmd
adb devices
scrcpy --always-on-top --window-title "Aegis Node" --max-fps 30
```
*(Note: `--max-fps 30` is highly recommended for older phones acting as compute nodes to save CPU overhead for your local GGUF models).*[cite: 1]

**Expected Output:**[cite: 1]
```text
* daemon not running; starting now at tcp:5037
* daemon started successfully
List of devices attached
02CAD8AD6B9B2F90    device
```
*Followed by the Scrcpy window mirroring the device display onto your laptop.*[cite: 1]