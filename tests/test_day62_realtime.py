import asyncio
import ssl
import os
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    pass
try:
    ssl.SSLContext._load_windows_store_certs = lambda self, storename, purpose: None
except Exception:
    pass

import socketio
import time

BASE = 'http://127.0.0.1:8001'

async def client_task(idx, message_queue, stop_after=6):
    sio = socketio.AsyncClient()
    received = 0

    @sio.event
    async def connect():
        print(f'Client {idx} connected')

    @sio.event
    async def disconnect():
        print(f'Client {idx} disconnected')

    @sio.on('systemStatus:update')
    async def on_status(data):
        nonlocal received
        received += 1
        message_queue.append((idx, 'systemStatus', data.get('timestamp')))

    @sio.on('sensor:reading')
    async def on_reading(data):
        nonlocal received
        received += 1
        message_queue.append((idx, 'sensor', data.get('timestamp')))

    await sio.connect(BASE + '/socket.io')
    start = time.time()
    while time.time() - start < stop_after:
        await asyncio.sleep(0.5)
    await sio.disconnect()
    return received


def run_test(clients=5):
    loop = asyncio.get_event_loop()
    message_queue = []
    tasks = [client_task(i, message_queue) for i in range(clients)]
    results = loop.run_until_complete(asyncio.gather(*tasks))
    print('Received counts per client:', results)
    print('Total messages received:', len(message_queue))

if __name__ == '__main__':
    run_test(5)
