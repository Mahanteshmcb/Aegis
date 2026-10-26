# Test core imports without services
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models_db import Tenant, User, Sensor, Zone
from backend.models.zones import Zone as Zone2
print("Core imports successful")
print("Zone from database:", Zone.__name__)
print("Zone from models.zones:", Zone2.__name__)