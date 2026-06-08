#Software Laboratory Part 3, Exercise 13
import time
import json
import threading
import requests
from es5e6_Lorenzo_con_modifiche_di_paolo import *
import paho.mqtt.client as mqtt

class SmartHomeController(object):
    exposed=True

    def __init__(self):
        self.catalog= Catalog
        self.fm=self.catalog.getFileManager()
        self.id= self.catalog.getDeviceID()
        body={}
        body["ID"]=self.id
        self.catalog.add(body)

        self.broker = "iot.eclipse.org" 
        self.port = 1883
        self.mqtt_client = mqtt.Client(client_id="SmartHomeEventController")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        try:
            self.mqtt_client.connect(self.broker, self.port, 60)
            self.mqtt_client.loop_start()
            print(f"MQTT Connected to {self.broker}:{self.port}\n")
        except Exception as e:
            print(f"MQTT Not Connected {e}\n")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker.")
            self.mqtt_client.subscribe("/tiot/group6/temperature")
            self.mqtt_client.subscribe("/tiot/group6/led")
            print("Subscribed to Arduino Sensors Topics.")
        else:
            print(f"Failed to connect to MQTT broker, return code {rc}\n")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            sensor_data = json.loads(payload)
            print("MQTT Received")
        except Exception as e:
            print(f"MQTT Error: {e}")