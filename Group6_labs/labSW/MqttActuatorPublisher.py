#Software Laboratory Part 3, Exercise 11
import time
import json
import threading
import requests
import paho.mqtt.client as mqtt

CATALOG_URL = "http://localhost:8080/catalog"
SERVICE_ID = "s000002"

class MqttActuatorPublisher:
    def __init__(self):
        self.catalog_devices = {}
        self.broker_ip = "broker.hivemq.com"
        self.broker_port = 1883
        self.running = True
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=SERVICE_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message


    def discover(self):
        print("Querying Catalog")
        try:
            response = requests.get(CATALOG_URL)
            if response.status_code == 200:
                catalog_data = response.json()
                broker_info = catalog_data.get("broker", {})
                self.broker_ip = broker_info.get("ip", self.broker_ip)
                self.broker_port = broker_info.get("port", self.broker_port)
                self.catalog_devices = catalog_data.get("devices", {}) 
                print(f"Broker: {self.broker_ip}:{self.broker_port}")
                print(f"Discovered {len(self.catalog_devices)} devices: {list(self.catalog_devices.keys())}")
            else:
                print(f"Catalog error: {response.status_code}")
        except Exception as e:
            print(f"Catalog discovery failed: {e}")

    def register_service(self):
            print("Registering service to Catalog...")
            payload = {
                "ID": SERVICE_ID,
                "description": "Interactive MQTT Actuator Command Publisher",
                "endpoints": ["MQTT"],
                "resources": ["thermostat", "arduino_led"]
            }
            try:
                requests.post(CATALOG_URL, json=payload)
                print(f"[SUCCESS] Service registered.")
            except Exception as e:
                print(f"[ERROR] Could not register service: {e}")

    def refresh_registration(self):
        while True:
            payload = {"ID": SERVICE_ID}
            try:
                requests.put(CATALOG_URL, json=payload)
                print("[keep-alive] Registration refreshed")
            except Exception as e:
                print(f"Failed to refresh: {e}")
            time.sleep(60)

    def on_connect(self, client, userdata, flags, rc):
            if rc == 0:
                print(f"Connected to MQTT broker at {self.broker_ip}:{self.broker_port}")
                # Subscribe al topic feedback Arduino (LED)
                client.subscribe("/tiot/group6/led")
                # Subscribe ai feedback dei software actuators
                client.subscribe("smart_home/actuators/+/feedback")
                print("Subscribed to feedback topics")
            else:
                print(f"Failed to connect to MQTT broker, return code {rc}")

    def on_message(self, client, userdata, msg):
            print(f"\n[FEEDBACK] {msg.topic} -> {msg.payload.decode()}")
            print("\n\n\nSelect an option (\n 1. Send command to Arduino LED \n2. Send command to Software Actuator (thermostat/lights/blinds) \n3. Show Discovered Devices\n4. Refresh devices from Catalog\n5. Exit\n", end="", flush=True)

    def _get_arduino_topic(self, actuator):
        topics = {
            "led": "/tiot/group6/led",
            "temperature": "/tiot/group6/temperature",
        }
        return topics.get(actuator, None)

    def _get_software_topic(self, actuator):
        #Topic (es13)
        return f"smart_home/actuators/{actuator}/command"

    def menu(self):
            while self.running:
                print(" MQTT Actuator Command Interface: ")
                print("1. Send command to Arduino LED")
                print("2. Send command to Software Actuator (thermostat/lights/blinds)")
                print("3. Show Discovered Devices")
                print("4. Refresh devices from Catalog")
                print("5. Exit")
                
                choice = input("\nSelect an option: ").strip()
                
                if choice == '1':
                    value = input("LED value (1=ON, 0=OFF): ").strip()
                    try:
                        v = int(value)
                        if v not in (0, 1):
                            print("Not valid value, use 0 or 1")
                            continue
                    except ValueError:
                        print("Insert 0 o 1")
                        continue
                    payload = {
                        "bn": "arduino_d001",
                        "e": [{"n": "led", "v": v, "u": "boolean", "t": time.time()}]
                    }
                    topic = "/tiot/group6/led"
                    self.client.publish(topic, json.dumps(payload))
                    print(f"Command published to {topic}: LED={'ON' if v==1 else 'OFF'}")

                elif choice == '2':
                    print("Actuators: thermostat, lights, blinds")
                    actuator = input("Enter actuator type: ").lower().strip()
                    value = input(f"Enter value for {actuator}: ").strip()
                    
                    try:
                        v = float(value) if '.' in value else int(value)
                    except ValueError:
                        v = value  

                    payload = {
                        "bn": f"actuator/",
                        "e": [{"n": actuator, "v": v, "u": "", "t": time.time()}]
                    }
                    topic = self._get_software_topic(actuator)
                    self.client.publish(topic, json.dumps(payload))
                    print(f"Command published to {topic}")

                elif choice == '3':
                    if not self.catalog_devices:
                        print("No devices found.")
                    else:
                        for d_id, info in self.catalog_devices.items():
                            print(f"\nID: {d_id}")
                            print(f"  Description: {info.get('Description', info.get('description',''))}")
                            print(f"  MQTT pub: {info.get('MQTT_topic_pub','N/A')}")
                            print(f"  MQTT sub: {info.get('MQTT_topic_sub','N/A')}")

                elif choice == '4':
                    self.discover()

                elif choice == '5':
                    print("Exiting...")
                    self.running = False
                    self.client.loop_stop()
                    self.client.disconnect()
                else:
                    print("Invalid choice, try again.")

    def start(self):
            self.discover()
            
            self.register_service()
            
            threading.Thread(target=self.refresh_registration, daemon=True).start()
            
            print(f"Connecting to broker {self.broker_ip}")
            try:
                self.client.connect(self.broker_ip, self.broker_port, 60)
                self.client.loop_start()
                time.sleep(1)
            except Exception as e:
                print(f"Unable to connect to broker: {e}")
                
            self.menu()

if __name__ == "__main__":
    publisher = MqttActuatorPublisher()
    publisher.start()