import threading
import time
import json
import random
import requests  
import paho.mqtt.client as mqtt



'''
COMANDI:


'''

URL = "http://localhost:8080/"


class DeviceMQTTClient:
    def __init__(self,device_id = "d000001"):
        self.ip,self.port = self.get_broker_info()
        self.device_id = device_id
        self.publish_interval = 30 #standard base


        self.topic_publish = f"iot/devices/{self.device_id}/temperature"
        self.topic_command = f"iot/devices/{self.device_id}/commands"
        
        self.register_to_catalog()

        self.client = mqtt.Client(client_id=device_id)
        self.client.on_message = self.message_menager
        
        try:
            self.client.connect(self.ip,self.port, 60)
            self.client.loop_start()
            print("MQTT Connected\n")
            self.client.subscribe(self.topic_command)
            print("Subscribed to commands")
        except Exception as e:
            print(f"MQTT Not Connected {e}\n")
        
    def get_broker_info(self):
        try:
            response = requests.get(URL)
            response.raise_for_status()
            catalog = response.json()
            broker = catalog.get("brocker",{})
            return broker.get("ip","localhost"),broker.get("port",1883)
        except Exception as e:
            print(f"Connection error: {e} using standard data")
            return "localhost",1883

    def register_to_catalog(self):
        payload = {
            "ID": self.device_id,
            "Description": "MQTT Temperature Publisher Node",
            "MQTT_topic": self.topic_publish,
            "Resources": ["temperature"]
        }
        try:
            requests.post(URL,json= payload)
            print("registrtion done")
        except Exception as e:
            print(f"registation error: {e}")

    def update_registration(self):
        payload = {
            "ID": self.device_id,
            "Description": "MQTT Temperature Publisher Node",
            "MQTT_topic": self.topic_publish,
            "Resources": ["temperature"]
        }
        try:
            requests.put(URL,json= payload)
            print("update done")
        except Exception as e:
            print(f"update error: {e}")

    def message_menager(self, client, userdata, msg): 
        print(f"Command recive: {msg.topic}") 
        try:
            message = msg.payload.decode('utf-8')
            message = json.loads(message)
            if ("publish_interval" in message):
                self.publish_interval = message["publish_interval"]
                print(f"new interval {self.publish_interval}")
        except Exception as e:
            print(f"Unknown command : {e}") 


    def start(self):
        def keep_alive():
            while True:
                self.update_registration()
                time.sleep(60)
        
        threading.Thread(target=keep_alive, daemon=True).start()
        
        #main loop
        while True:
            temp = round(random.uniform(18.0, 25.0), 2)
            payload = [{
                "bn" : self.device_id,
                "n" : "temperature",
                "v" : temp,
                "u" : "Cel",
                "t" : time.time()
            }]
            payload_json = json.dumps(payload)
            self.client.publish(self.topic_publish,payload_json)
            print("MQTT publish")
            time.sleep(self.publish_interval)

    

if __name__ == "__main__":
    sensor_node = DeviceMQTTClient(device_id="d000001")
    sensor_node.start()