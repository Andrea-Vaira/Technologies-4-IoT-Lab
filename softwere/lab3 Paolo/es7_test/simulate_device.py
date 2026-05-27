import paho.mqtt.client as mqtt
import json
import time

# 1. Configurazione del client MQTT
client = mqtt.Client()
client.connect("localhost", 1883, 60)

# Dati del dispositivo fittizio
device_data = {
    "ID": "d000001",
    "Description": "Sensore Temperatura Salotto",
    "Rest endpoint URL": "http://192.168.1.50:5000",
    "MQTT info": {"ip": "localhost", "port": 1883, "topic": "salotto/temp"},
    "Resources List": ["temperature"]
}

print("Dispositivo IoT avviato. Invio keep-alive ogni 30 secondi...")

try:
    while True:
        # Trasformiamo il dizionario in stringa JSON
        payload = json.dumps(device_data)
        
        # Pubblichiamo sul topic a cui il server è iscritto
        client.publish("catalog/update/devices", payload)
        print(f"[{time.strftime('%H:%M:%S')}] Messaggio MQTT inviato per {device_data['ID']}")
        
        time.sleep(30)
except KeyboardInterrupt:
    print("Simulazione interrotta.")