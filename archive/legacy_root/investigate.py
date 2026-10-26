#!/usr/bin/env python3
# Investigate Zone class imports
import sys

# Import just what services import
from backend import models_db as models_db

# Check what Zone we get
print("models_db.Zone.__name__:", models_db.Zone.__name__)

# Check if models.zones.Zone is also importable without causing issues
try:
    from backend.models.zones import Zone as ZoneModels
    print("ZoneModels.__name__:", ZoneModels.__name__)
    print("Are they the same?", models_db.Zone is ZoneModels)
except Exception as e:
    print("Error importing ZoneModels:", e)