# IoT Edge Code for ESP32
# MicroPython example for sensor reading

import machine
import time
import network
from umqtt.simple import MQTTClient

# WiFi credentials
SSID = 'your_ssid'
PASSWORD = 'your_password'

# MQTT broker
MQTT_BROKER = '192.168.1.100'  # Raspberry Pi gateway
CLIENT_ID = 'esp32_sensor'

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)
    print('WiFi connected')

def main():
    connect_wifi()
    client = MQTTClient(CLIENT_ID, MQTT_BROKER)
    client.connect()

    # Example sensor (DHT22)
    dht_pin = machine.Pin(4)
    dht = machine.DHT22(dht_pin)

    while True:
        dht.measure()
        temp = dht.temperature()
        hum = dht.humidity()
        payload = f'{{"temperature": {temp}, "humidity": {hum}}}'
        client.publish(b'sensor/data', payload)
        time.sleep(60)  # Send every minute

if __name__ == '__main__':
    main()