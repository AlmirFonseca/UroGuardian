import paho.mqtt.client as mqtt
import json
import matplotlib.pyplot as plt
from datetime import datetime

BROKER = "192.168.0.168"
PORT = 1883
TOPIC = "spectrumdatapoints"

# Custom x labels after removing the 5th and 6th samples
sample_labels = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "Clear", "NIR"]

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    data = json.loads(payload)
    color_map = {'R': 'red', 'G': 'green', 'B': 'blue', 'W': 'black'}
    lines_data = {}
    timestamp = None
    
    for dp in data['batch']:
        color = dp['ledcolor']
        channels = dp['channels']
        if color in color_map:
            # Remove 5th and 6th samples (index 4 and 5)
            filtered_channels = channels[:4] + channels[6:]
            lines_data[color] = filtered_channels
            timestamp = dp['timestamp']
    
    plt.figure(figsize=(10, 5))
    for key, val in lines_data.items():
        plt.plot(sample_labels, val, label=key, color=color_map[key], marker='o')
    
    plt.title(f"Spectrum Channels | Timestamp: {timestamp}")
    plt.xlabel("Sample")
    plt.ylabel("Value")
    plt.legend(["Red", "Green", "Blue", "White"], loc='best')
    plt.grid(True)
    
    ts_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S")
    filename = f"spectrum_lines_{ts_str}.png"
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"Saved line plot at {filename}")

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe(TOPIC)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)

print("Listening for MQTT messages. Ctrl+C to quit.")
client.loop_forever()
