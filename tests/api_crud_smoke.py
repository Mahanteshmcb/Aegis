from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

print('Login...')
resp = client.post('/api/v1/auth/login', data={'username':'admin@aegis.com','password':'admin1234'})
print('login', resp.status_code, resp.text)
if resp.status_code != 200:
    raise SystemExit('Login failed')

token = resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

print('Create zone...')
resp = client.post('/api/v1/zones', json={'name':'API Test Zone','description':'test'}, headers=headers)
print('create zone', resp.status_code, resp.text)
if resp.status_code >= 400:
    raise SystemExit('Create zone failed')

zone = resp.json()
zone_id = zone['id']

print('Update zone...')
resp = client.put(f'/api/v1/zones/{zone_id}', json={'description':'updated via test'}, headers=headers)
print('update zone', resp.status_code, resp.text)

print('Create sensor...')
resp = client.post('/api/v1/sensors', json={'name':'API Sensor','type':'temperature','zone_id':zone_id}, headers=headers)
print('create sensor', resp.status_code, resp.text)
if resp.status_code < 400:
    sensor_id = resp.json()['id']
    print('Delete sensor...')
    resp = client.delete(f'/api/v1/sensors/{sensor_id}', headers=headers)
    print('delete sensor', resp.status_code, resp.text)

print('Delete zone...')
resp = client.delete(f'/api/v1/zones/{zone_id}', headers=headers)
print('delete zone', resp.status_code, resp.text)

print('Done')
