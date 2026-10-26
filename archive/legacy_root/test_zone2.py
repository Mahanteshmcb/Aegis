#!/usr/bin/env python3
from backend.database import Zone as ZoneDB
from backend.models.zones import Zone as ZoneModels
print("ZoneDB name:", ZoneDB.__name__)
print("ZoneModels name:", ZoneModels.__name__)
print("ZoneModels table_args:", ZoneModels.__table_args__)
print("Are they the same?", ZoneDB is ZoneModels)