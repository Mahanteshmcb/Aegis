# Script to update estate_config router imports
with open('C:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\routers\\estate_config.py', 'r') as f:
    content = f.read()

old_import = 'from backend.ai.orchestrator import evaluate_reading'
new_imports = '''from backend.ai.orchestrator import evaluate_reading
from backend.database import get_db, Device, Zone, EstateConfig, device_zone, Engine'''

if old_import in content:
    content = content.replace(old_import, new_imports, 1)
    with open('C:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis\\backend\\routers\\estate_config.py', 'w') as f:
        f.write(content)
    print('SUCCESS: Imports updated')
else:
    print('Target import not found')