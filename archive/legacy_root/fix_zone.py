#!/usr/bin/env python3
import re

# Fix database.py - replace string Zone references with actual class
with open('c:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\database.py', 'r') as f:
    content = f.read()

# Replace both occurrences of zone = relationship("Zone", foreign_keys=[zone_id])
content = content.replace('zone = relationship("Zone", foreign_keys=[zone_id])', 'zone = relationship(Zone)')

with open('c:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\database.py', 'w') as f:
    f.write(content)

print('Fixed database.py')

# Fix models/environmental.py
with open('c:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\models\\environmental.py', 'r') as f:
    content = f.read()

# Replace zone = relationship("Zone", back_populates="environmental_zone")
content = content.replace('zone = relationship("Zone", back_populates="environmental_zone")', 'zone = relationship(Zone)')

with open('c:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\models\\environmental.py', 'w') as f:
    f.write(content)

print('Fixed environmental.py')

# Fix models/hvac_schedule.py
with open('c:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\models\\hvac_schedule.py', 'r') as f:
    content = f.read()

# Replace zone = relationship("Zone")
content = content.replace('zone = relationship("Zone")', 'zone = relationship(Zone)')

with open('c:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\models\\hvac_schedule.py', 'w') as f:
    f.write(content)

print('Fixed hvac_schedule.py')

# Fix models_db.py - replace remaining "Zone" string references with actual Zone class
# Need to check what Zone is available in this context
with open('c:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\models_db.py', 'r') as f:
    content = f.read()

# These need careful handling - check if Zone is imported
# Pattern: zone = relationship("Zone", foreign_keys=[zone_id])
# Should become: zone = relationship(Zone) if Zone is imported from backend.database

# Let's just replace the straightforward ones where Zone class is available
content = content.replace('zone = relationship("Zone", foreign_keys=[zone_id])', 'zone = relationship(Zone)')

with open('c:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\models_db.py', 'w') as f:
    f.write(content)

print('Fixed models_db.py')

print('All Zone string references fixed!')