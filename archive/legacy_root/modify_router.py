# Script to enhance estate_config router
with open('C:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\routers\\estate_config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add evaluate_reading import after the existing imports
old_import_text = """from backend.database import get_db, Device, Zone, EstateConfig, device_zone, Engine
from backend.estate_config import load_and_persist, get_spatial_graph"""

new_import_text = """from backend.database import get_db, Device, Zone, EstateConfig, device_zone, Engine
from backend.estate_config import load_and_persist, get_spatial_graph
from backend.ai.orchestrator import evaluate_reading"""

if old_import_text in content:
    content = content.replace(old_import_text, new_import_text, 1)
    print('Step 1: Added evaluate_reading import - SUCCESS')
else:
    print('Step 1: FAIL - Could not find import text to replace')
    # Debug: show what we have
    idx = content.find('from backend.database import')
    if idx >= 0:
        print(f'Found at position {idx}: {repr(content[idx:idx+80])}')

# 2. Add Pydantic models after the router setup
models_marker = 'router = APIRouter(prefix="/api/v1/estate-config", tags=["estate-config"])\n'
models_to_add = '''

# Pydantic models for API requests/responses

class DeviceCreate(BaseModel):
    """Schema for creating a new device in the digital twin."""
    device_id: str = Field(..., description="Unique device identifier")
    type: str = Field(..., description="Device type: sensor, rover, zone, actuator")
    subtype: Optional[str] = Field(None, description="Sensor or rover subtype")
    zone_id: Optional[str] = Field(None, description="Target zone ID")
    position: Optional[Dict[str, float]] = Field(
        None, description="Position in digital twin coordinates (x, y, z)"
    )
    status: Optional[str] = Field("idle", description="Initial status")
    asset_ratio: Optional[str] = Field(
        None, description="Model-to-real-world ratio (e.g., '1:100')"
    )
    battery_level: Optional[float] = Field(
        None, description="Battery level 0-100 (rovers only)"
    )
    payload_capacity: Optional[str] = Field(
        None, description="Payload capacity (rovers only), e.g., '20kg'"
    )
    max_speed_m_s: Optional[float] = Field(
        None, description="Max speed in m/s (rovers only)"
    )
    dimensions: Optional[Dict[str, float]] = Field(
        None, description="Device dimensions (length, width, height)"
    )
    threshold_low: Optional[float] = Field(None, description="Low threshold")
    threshold_high: Optional[float] = Field(None, description="High threshold")
    units: Optional[str] = Field("%", description="Units for readings")
    environment_data: Optional[Dict] = Field(None, description="Environment data JSON")


class DeviceUpdate(BaseModel):
    """Schema for updating device status and properties."""
    position: Optional[Dict[str, float]] = Field(None, description="New position")
    status: Optional[str] = Field(None, description="New status")
    last_reading: Optional[float] = Field(None, description="New sensor reading")
    units: Optional[str] = Field(None, description="New units")
    battery_level: Optional[float] = Field(
        None, description="Battery level 0-100 (rovers)"
    )
    payload_capacity: Optional[str] = Field(
        None, description="New payload capacity (rovers)"
    )
    max_speed_m_s: Optional[float] = Field(
        None, description="New max speed (rovers)"
    )
    asset_ratio: Optional[str] = Field(None, description="New asset ratio")
    threshold_low: Optional[float] = Field(None, description="New low threshold")
    threshold_high: Optional[float] = Field(None, description="New high threshold")
    environment_data: Optional[Dict] = Field(None, description="New environment data")


class ZoneCreate(BaseModel):
    """Schema for creating/updating a zone."""
    zone_id: str = Field(..., description="Unique zone identifier")
    name: Optional[str] = Field(None, description="Zone name")
    coordinates: Optional[Dict] = Field(
        None, description="Zone coordinates {x, y, width_meters, depth_meters}"
    )
    asset_ratio: Optional[str] = Field(
        "1:100", description="Model-to-real-world ratio"
    )


class SensorEvaluation(BaseModel):
    """Schema for sensor reading evaluation."""
    sensor_type: str = Field(..., description="Type of sensor (soil_moisture, temperature, etc.)")
    value: float = Field(..., description="Sensor reading value")
    zone_id: str = Field(..., description="Zone ID to evaluate against")'''

if models_marker in content:
    # Insert after the router line
    insert_pos = content.index(models_marker) + len(models_marker)
    content = content[:insert_pos] + models_to_add + content[insert_pos:]
    print('Step 2: Added Pydantic models - SUCCESS')
else:
    print('Step 2: FAIL - Could not find router marker')

# 3. Write the modified content back
with open('C:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\routers\\estate_config.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Script completed - file written')