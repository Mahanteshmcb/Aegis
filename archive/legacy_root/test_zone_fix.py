import sys
sys.path.insert(0, 'c:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis')
from backend.models.zones import Zone
print('Zone import successful:', Zone.__tablename__)
print('Zone columns:', [c.name for c in Zone.__table__.columns])
d = Zone(zone_id='test1', name='Test Zone')
print('to_dict:', d.to_dict())