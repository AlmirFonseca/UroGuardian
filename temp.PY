import paho.mqtt.client as mqtt
import json
from datetime import datetime
import random
import time

broker = "192.168.0.168"
port = 1883

client = mqtt.Client()
client.connect(broker, port)
client.loop_start()

def gerar_system_telemetry():
    return {
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "cpu_usage": round(random.uniform(0, 100), 2),
        "cpu_temp": round(random.uniform(30, 90), 2),
        "ram_usage": round(random.uniform(0, 100), 2),
        "disk_usage": round(random.uniform(0, 100), 2),
        "battery_level": round(random.uniform(0, 100), 2),
        "network_usage": round(random.uniform(0, 10), 2),
        "wifi_ssid": "ExampleWiFi",
        "wifi_signal_strength": round(random.uniform(-100, -30), 2)
    }

def gerar_logs():
    return {
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "error_code": "E_101",
        "error_message": "Sensor desconectado"
    }

def gerar_spectrum_datapoint(mac, batch, led_color, flag):
    # Retorna 1 datapoint/led
    return {
        "mac_address": mac,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "batch": batch,
        "flag": flag,
        "led_color": led_color,
        "led_intensity": random.randint(0, 100),
        "channel_415nm": random.randint(1000, 2000),
        "channel_445nm": random.randint(1000, 2000),
        "channel_480nm": random.randint(1000, 2000),
        "channel_515nm": random.randint(1000, 2000),
        "channel_555nm": random.randint(1000, 2000),
        "channel_590nm": random.randint(1000, 2000),
        "channel_630nm": random.randint(1000, 2000),
        "channel_680nm": random.randint(1000, 2000),
        "channel_clear": random.randint(1000, 2000),
        "channel_nir": random.randint(1000, 2000)
    }

mac = "AA:BB:CC:DD:EE:FF"
cores_usadas = ["R", "G", "B", "W", "IR"]

# Envio de system telemetry/logs de exemplo
# client.publish("system_telemetry", json.dumps(gerar_system_telemetry()))
# client.publish("logs", json.dumps(gerar_logs()))

num_samples = 1
for n in range(num_samples):
    num_batches = 1
    for batch in range(1, num_batches + 1):
        for i, led_color in enumerate(cores_usadas):
            # Flags: primeiro datapoint do ciclo FLAG=1, intermediário FLAG=0, último FLAG=-1
            if batch == 1 and i == 0:
                flag = 1
            elif batch == num_batches and i == len(cores_usadas) - 1:
                flag = -1
            else:
                flag = 0
            datapoint = gerar_spectrum_datapoint(mac, batch, led_color, flag)
            client.publish("spectrum_datapoints", json.dumps(datapoint))
            print(f"Enviando batch={batch} cor={led_color} flag={flag}")

            # Opcional: intervalo para simular tráfego real
            time.sleep(0.2)

client.loop_stop()
client.disconnect()
print("Mensagens fake enviadas com sucesso.")
