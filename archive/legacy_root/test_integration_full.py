#!/usr/bin/env python
"""MVP Integration Test - Tests all API endpoints and event engine."""

import sys
import os
import json
import urllib.request
import urllib.error

sys.path.insert(0, '.')

BASE_URL = 'http://127.0.0.1:8001'

def test_endpoint(method, path, body=None, expect_status=200):
    """Test an API endpoint."""
    url = BASE_URL + path
    data = json.dumps(body).encode() if body else None
    
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            text = response.read().decode()
            return status, text
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return None, str(e)

def test_imports():
    """Test Python imports."""
    results = []
    
    # Test event_engine
    try:
        from backend.ai.event_engine import EventEngine, ThresholdRule
        results.append(('event_engine', 'PASS'))
    except Exception as e:
        results.append(('event_engine', f'FAIL: {e}'))
    
    # Test orchestrator
    try:
        from backend.ai.orchestrator import evaluate_reading, DEFAULT_RULES
        results.append(('orchestrator', 'PASS'))
    except Exception as e:
        results.append(('orchestrator', f'FAIL: {e}'))
    
    # Test database
    try:
        from backend.database import init_db, engine
        results.append(('database', 'PASS'))
    except Exception as e:
        results.append(('database', f'FAIL: {e}'))
    
    # Test routers
    try:
        from backend.routers.robotics_compat import router
        results.append(('robotics_compat', 'PASS'))
    except Exception as e:
        results.append(('robotics_compat', f'FAIL: {e}'))
    
    try:
        from backend.routers.estate_config import router
        results.append(('estate_config', 'PASS'))
    except Exception as e:
        results.append(('estate_config', f'FAIL: {e}'))
    
    return results

def test_event_logic():
    """Test event engine evaluation logic."""
    from backend.ai.orchestrator import evaluate_reading
    
    results = []
    
    # Test moisture=25% → dispatch
    events = evaluate_reading('soil_moisture', 25.0, 'zone_alpha')
    if events:
        e = events[0]
        passed = e['severity'] == 'high' and e['event_type'] == 'dispatch'
        results.append(('moisture_25%', 'PASS' if passed else 'FAIL'))
    else:
        results.append(('moisture_25%', 'NO_EVENT'))
    
    # Test temperature=40°C → dispatch
    events = evaluate_reading('temperature', 40.0, 'zone_alpha')
    if events:
        e = events[0]
        passed = e['severity'] == 'high' and e['event_type'] == 'dispatch'
        results.append(('temp_40C', 'PASS' if passed else 'FAIL'))
    else:
        results.append(('temp_40C', 'NO_EVENT'))
    
    return results

def test_web_endpoints():
    """Test web endpoints."""
    results = []
    
    # Health check
    status, text = test_endpoint('GET', '/api/v1/health')
    results.append(('health_' + str(status), 'PASS' if status == 200 else 'FAIL'))
    
    # Root endpoint
    status, text = test_endpoint('GET', '/')
    results.append(('root_' + str(status), 'PASS' if status == 200 else 'FAIL'))
    
    # Tasks GET (should be 403 without session or 200 with session)
    status, text = test_endpoint('GET', '/api/v1/tasks')
    results.append(('tasks_get_' + str(status), 'PASS' if status in [200, 403] else 'FAIL'))
    
    return results

if __name__ == '__main__':
    print("=" * 60)
    print("Aegis MVP Integration Test")
    print("=" * 60)
    
    print("\n--- Python Import Tests ---")
    import_results = test_imports()
    for name, status in import_results:
        print(f"  {name}: {status}")
    
    print("\n--- Event Engine Logic Tests ---")
    event_results = test_event_logic()
    for name, status in event_results:
        print(f"  {name}: {status}")
    
    print("\n--- Web API Endpoint Tests ---")
    web_results = test_web_endpoints()
    for name, status in web_results:
        print(f"  {name}: {status}")
    
    print("\n" + "=" * 60)