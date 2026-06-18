# test_sub.py — salva in labSW\
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connesso!" if rc == 0 else f"Errore rc={rc}")
    client.subscribe("/tiot/group6/temperature")
    print("In ascolto su /tiot/group6/temperature ...")

def on_message(client, userdata, msg):
    print(f"[{msg.topic}] {msg.payload.decode()}")

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "test_subscriber_pc")
c.on_connect = on_connect
c.on_message = on_message
c.connect("broker.hivemq.com", 1883, 60)
c.loop_forever()