import requests
resp = requests.post('http://127.0.0.1:8001/api/v1/auth/login', json={'email':'admin@aegis.com','password':'admin1234'})
print('STATUS', resp.status_code)
try:
    print(resp.json())
except Exception:
    print(resp.text)
