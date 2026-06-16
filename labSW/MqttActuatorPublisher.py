import time
import json
import threading
import requests
import paho.mqtt.client as mqtt

CATALOG_URL = "http://localhost:8080/"
SERVICE_ID = "s000002"

class MqttActuatorPublisher:
    def __init__(self):
        self.catalog_devices = {}
        self.broker_ip = "iot.eclipse.org"
        self.broker_port = 1883
        self.running = True
        
        self.client = mqtt.Client(client_id=SERVICE_ID)
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
                print(f"Discovered {len(self.catalog_devices)} devices from Catalog.")
            else:
                print(f"Failed to fetch Catalog data. Status code: {response.status_code}")
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
                print("[SUCCESS] Service registered.")
            except Exception as e:
                print(f"[ERROR] Could not register service: {e}")

    def refresh_registration(self):
            while True:
                payload = {"ID": SERVICE_ID}
                try:
                    requests.put(CATALOG_URL, json=payload)
                except Exception as e:
                    print(f"Failed to refresh catalog registration: {e}")
                time.sleep(60)

    def on_connect(self, client, userdata, flags, rc):
            if rc == 0:
                print(f"Connected to MQTT broker at {self.broker_ip}:{self.broker_port}")
                feedback_topic = "smart_home/+/feedback" 
                client.subscribe(feedback_topic) #needs implementation
                print(f"Subscribed to feedback topic: {feedback_topic}")
            else:
                print(f"Failed to connect to MQTT broker, return code {rc}")

    def on_message(self, client, userdata, msg):
            print(f"{msg.topic} -> {msg.payload.decode()}")
            print("Select an option (1: Send Command, 2: Refresh Catalog, 3: Exit): ", end="", flush=True)


    def menu(self):
            while self.running:
                print(" MQTT Actuator Command Interface: ")
                print("1. Send Actuation Command")
                print("2. Show Discovered Devices")
                print("3. Exit")
                
                choice = input("\nSelect an option: ")
                
                if choice == '1':
                    actuator = input("Enter actuator type (e.g., thermostat, led): ").lower()
                    value = input(f"Enter target value for {actuator} (e.g., 'on', 'off', 22, 50): ")
                    if value.isnumeric():
                        value = float(value)
                
                    #JSON payload
                    cmd_payload = {
                        "e": {
                            "n": actuator,
                            "v": value,
                            "t": time.time()
                        }
                    }
                    
                    #needs to be adapted
                    topic = f"smart_home/actuators/{actuator}/command"
                    
                    self.client.publish(topic, json.dumps(cmd_payload))
                    print(f"Command published to {topic}")
                    
                elif choice == '2':
                    if not self.catalog_devices:
                        print("No devices found or Catalog is offline.")
                    for d_id, info in self.catalog_devices.items():
                        print(f"ID: {d_id} | Info: {info}")
                        
                elif choice == '3':
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
            except Exception as e:
                print(f"Unable to connect to broker: {e}")
                
            self.menu()













if __name__ == "__main__":
    publisher = MqttActuatorPublisher()
    publisher.start()