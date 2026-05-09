# Aegis Architecture Diagrams

This directory contains Mermaid source files (`.mmd`) and generated high-resolution PNG images.

## Current Diagrams

- `01_system_architecture.mmd` → `01_system_architecture_hires.png`
- `02_sensor_actuator_flow.mmd` → `02_sensor_actuator_flow_hires.png`
- `03_hardware_stack.mmd` → `03_hardware_stack_hires.png`
- `04_multi_robot_coordination.mmd` → `04_multi_robot_coordination_hires.png`
- `05_network_protocols.mmd` → `05_network_protocols_hires.png`
- `06_mission_lifecycle.mmd` → `06_mission_lifecycle_hires.png`

## Converting a Single New Diagram

When you add a new `.mmd` file (e.g., `my_new_diagram.mmd`), convert it to high-resolution PNG with this command:

```cmd
cd /d C:\Users\Mahantesh\DevelopmentProjects\Aegis
set "PUPPETEER_EXECUTABLE_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
node_modules\.bin\mmdc -i diagrams\my_new_diagram.mmd -o diagrams\my_new_diagram_hires.png -w 2400 -H 1800 -s 2
```

**Replace `my_new_diagram` with your actual filename.**

## Batch Convert All Diagrams

To convert all `.mmd` files in this folder to high-resolution PNGs:

```cmd
cd /d C:\Users\Mahantesh\DevelopmentProjects\Aegis
set "PUPPETEER_EXECUTABLE_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
for %F in (diagrams\*.mmd) do node_modules\.bin\mmdc -i "%F" -o "%~dpnF_hires.png" -w 2400 -H 1800 -s 2
```

## Mermaid CLI Installation

If Mermaid CLI is not installed, run this once:

```cmd
npm install @mermaid-js/mermaid-cli --save-dev
```

## Notes

- `-w 2400 -H 1800` sets a large canvas size for high resolution
- `-s 2` doubles the render scale for crisp text and lines
- Output files use `_hires.png` suffix to avoid overwriting originals
- Requires Chrome browser installed at default location

## Viewing Diagrams

- **High-res PNGs**: Open directly in any image viewer
- **Mermaid source**: Edit `.mmd` files and re-convert
- **GitHub**: `.mmd` files render automatically as diagrams