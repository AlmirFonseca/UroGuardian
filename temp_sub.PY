import paho.mqtt.client as mqtt

broker = "192.168.0.168"
port = 1883

# Callback para quando uma mensagem chega
def on_message(client, userdata, msg):
    print(f"Tópico: {msg.topic} | Mensagem: {msg.payload.decode('utf-8')}")

client = mqtt.Client()
client.on_message = on_message

client.connect(broker, port)

# Inscreve-se em todos os tópicos que você quer monitorar
client.subscribe("system_telemetry")
client.subscribe("logs")
client.subscribe("spectrum_datapoints")

print("Aguardando mensagens MQTT...\nPressione Ctrl+C para sair.")

# Loop infinito para manter a escuta ativa
client.loop_forever()
