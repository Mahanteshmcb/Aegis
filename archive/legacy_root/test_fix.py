import subprocess
import sys

proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8001'],
    cwd='C:\\Users\\Mahantesh\\DevelopmentProjects\\Aegis',
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

print(f'Started uvicorn with PID {proc.pid}')
print('Waiting for server to start...')

import time
time.sleep(3)

# Test the import and API
from backend.database import Device, Zone
print('Database import successful!')

import requests
try:
    resp = requests.get('http://127.0.0.1:8001/docs', timeout=3)
    print(f'API responding, status: {resp.status_code}')
except Exception as e:
    print(f'Server not ready yet: {e}')

proc.terminate()