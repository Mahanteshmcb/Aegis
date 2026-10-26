#!/usr/bin/env python3
from backend.database import Zone as ZoneDB
from backend.models.zones import Zone as ZoneModels
from backend.models_db import Tenant
from backend.models.environmental import EnvironmentalZone
from backend.models.hvac_schedule import HVACSchedule
print("ZoneDB:", ZoneDB.__name__)
print("ZoneModels:", ZoneModels.__name__)
print("All imports successful - no NameError!")