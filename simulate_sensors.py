import requests
import time
import random

BASE_URL = "http://localhost:8080/api/v1"
# Ensure these match your database exactly
LOGIN_DATA = {"email": "operator@aegis.com", "password": "aegispassword"} 

def get_token():
    # We use json= here because our new backend login handles JSON perfectly
    response = requests.post(f"{BASE_URL}/auth/login", json=LOGIN_DATA)
    if response.status_code != 200:
        print(f"❌ Login Failed! Status: {response.status_code}")
        print(f"Response: {response.text}")
        exit()
    return response.json()["access_token"]

def simulate():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 1. Get zones
    zones_resp = requests.get(f"{BASE_URL}/zones", headers=headers)
    zones = zones_resp.json()
    
    if not zones or zones_resp.status_code != 200:
        print("No zones found or unauthorized. Check backend logs.")
        return
    
    zone_id = zones[0]["id"]
    tenant_id = zones[0]["tenant_id"] # Dynamically get tenant_id
    print(f"📡 Targeting Zone: {zones[0]['name']} (ID: {zone_id})")

    # 2. Register a Sensor
    # FIXED: Added 'tenant_id' to satisfy the backend validation
    sensor_payload = {
        "name": "Aegis-Thermal-01",
        "type": "thermal",
        "location": "Ceiling Mount",
        "zone_id": zone_id,
        "tenant_id": tenant_id, 
        "status": "active"
    }
    
    sensor_resp = requests.post(f"{BASE_URL}/sensors", json=sensor_payload, headers=headers)
    
    if sensor_resp.status_code != 200:
        print(f"❌ Sensor Creation Failed: {sensor_resp.text}")
        return

    sensor = sensor_resp.json()
    sensor_id = sensor["id"]
    print(f"✅ Sensor Registered: ID {sensor_id}")

    # 3. Loop telemetry data
    print("🚀 Starting Live Telemetry Stream...")
    try:
        while True:
            # Note: Ensure your backend has a route: POST /api/v1/sensors/{id}/data
            telemetry = {
                "sensor_id": sensor_id,
                "value": round(random.uniform(21.0, 24.0), 2),
                "unit": "°C",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            data_resp = requests.post(f"{BASE_URL}/sensors/data", json=telemetry, headers=headers)
            
            if data_resp.status_code == 200:
                print(f"📊 Sent: {telemetry['value']}{telemetry['unit']} at {telemetry['timestamp']}")
            else:
                print(f"⚠️ Telemetry Error: {data_resp.status_code} - {data_resp.text}")
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

if __name__ == "__main__":
    simulate()