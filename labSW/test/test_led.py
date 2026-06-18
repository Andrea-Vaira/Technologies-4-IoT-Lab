# test_led.py
import paho.mqtt.client as mqtt, json, time

def on_connect(client, userdata, flags, rc):
    print("Connesso al broker!" if rc == 0 else f"Errore rc={rc}")

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "test_led_publisher")
c.on_connect = on_connect
c.connect("broker.hivemq.com", 1883, 60)
c.loop_start()
time.sleep(2)  # aspetta connessione

# Accendi
payload = {"bn":"arduino_d001","e":[{"n":"led","v":1,"u":"boolean","t":0}]}
result = c.publish("/tiot/group6/led", json.dumps(payload))
print(f"LED ON inviato, result={result.rc}")
time.sleep(5)  # aspetta consegna

# Spegni
payload["e"][0]["v"] = 0
result = c.publish("/tiot/group6/led", json.dumps(payload))
print(f"LED OFF inviato, result={result.rc}")
time.sleep(5)  # aspetta consegna

c.loop_stop()
c.disconnect()
print("Fine")