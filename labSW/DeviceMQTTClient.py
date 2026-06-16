import threading
import time
import json
import random
import requests  
import paho.mqtt.client as mqtt



'''
COMANDI:


python '.\softwere\lab3 Paolo\es7.py'
python '.\softwere\lab3 Paolo\es8.py'


'''

URL = "http://localhost:8080/"

class DeviceMQTTClient:
    def __init__(self):
        self.dID = 1
        self.sID = 1
        self.client = mqtt.Client()
        try:
            self.client.connect("localhost", 1883, 60)
            self.client.loop_start()
            print("MQTT Connected\n")
        except Exception as e:
            print(f"MQTT Not Connected {e}\n")
        threading.Thread(target=self._registration_loop, daemon=True).start()

    def start(self):
        while True:
            print("multiple choise menu \n1-> Send Register\n2-> see catalog\n3-> see specific device\n4-> quit")
            choise = input("Insert here: ").strip()
            match choise:
                case "1":
                    device_data = self.construct_record()
                    payload = json.dumps(device_data)
                    if (device_data["ID"][0] == 'd'):
                        self.client.publish("catalog/update/devices", payload)
                    else:
                        self.client.publish("catalog/update/services", payload)
                    print(f"[{time.strftime('%H:%M:%S')}] MQTT sended for {device_data['ID']}")

                case "2":
                    response = requests.get(URL)
                    try:
                        if response.status_code == 200:
                            print(json.dumps(response.json(), indent=4))
                        else:
                            print(f"Server error: {response.status_code}")
                    except Exception as e:
                        print(f" Connection error {e}\n")

                case "3":
                    target_id = input("Insert the specific ID to search (e.g., d000001): ")
                    try:
                        if response.status_code == 200:
                            catalog = response.json()
                            devices = catalog.get("devices", {})
                            services = catalog.get("services", {})
                            if target_id in devices:
                                print("FOUND")
                                print(json.dumps(devices[target_id],indent=4))
                            elif target_id in services:
                                print("FOUND")
                                print(json.dumps(devices[target_id],indent=4))    
                            else:
                                print("NOT FOUND")
                        else:
                            print(f"Server error: {response.status_code}")
                    except Exception as e:
                        print(f" Connection error {e}\n")

                case "4":
                    self.client.loop_stop()
                    break
                case _:
                    print("Command not resognized")


    def _registration_loop(self):
        while True:
            device_data = self.construct_record()
            payload = json.dumps(device_data)
            if (device_data["ID"][0] == 'd'):
                self.client.publish("catalog/update/devices", payload)
            else:
                self.client.publish("catalog/update/services", payload)
            print(f"[{time.strftime('%H:%M:%S')}] MQTT sended for {device_data['ID']}")
            time.sleep(60)


    def construct_record(self):
        device_data = {
            "Description": "Sensore Temperatura Salotto",
            "Rest endpoint URL": "http://192.168.1.50:5000",
            "MQTT info": {"ip": "localhost", "port": 1883, "topic": "salotto/temp"},
            "Resources List": ["temperature"]
        }       
        var = random.randint(1,2)
        if var == 1:
            device_data["ID"] = f"d{self.dID:06d}"
            self.dID += 1
        else:
            device_data["ID"] = f"s{self.sID:06d}"
            self.sID += 1
        return device_data
    


if __name__ == '__main__':
    simulator = DeviceMQTTClient()
    simulator.start()