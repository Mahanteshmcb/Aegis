#!/usr/bin/env python3
from backend.database import Zone as ZoneDB
from backend.models.zones import Zone as ZoneModels
print("ZoneDB:", ZoneDB.__name__)
print("ZoneModels:", ZoneModels.__name__)
print("Imports successful - no NameError!")