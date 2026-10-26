from backend.models.zones import Zone as Zone1
from backend.models_db import Tenant, User, Sensor, SensorData, AuditLog
from backend.database import Zone as Zone2
print("All imports successful")
print("Zone1 from models.zones:", Zone1.__name__)
print("Zone2 from database:", Zone2.__name__)
print("Tenant, User, Sensor imported from models_db successfully")