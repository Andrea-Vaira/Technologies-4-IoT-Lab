#Software Laboratory Part 3, Exercise 13
import time
import json
import threading
import requests
import cherrypy
import paho.mqtt.client as mqtt

catalog_url = "http://localhost:8080/catalog"

ALERT_THRESHOLD= 30 #Maximum temperature also used in the Arduino Lab 2.1
TIMEOUT_PIR = 2 * 60

class SmartHomeController(object):
    exposed=True

    def __init__(self):
        self.roomsReadings={} #List with the 10 last readings for each room
        self.num=0
        self.roomStatistics={}
        self.motionStatus=False
        self.configurable_threshold=26

        #Regitration over REST for the Catalog
        self.body = {
            "ID": "Controller_s00000",
            "description": "Service that controls the entire system"
        }

        try:
            requests.post(catalog_url, json=self.body) #Registers to the catalog via REST using POST
        except Exception as e:
            print("Error, Not Registred in the Catalog")
        threading.Thread(target=self.refreshRegistration_loop, daemon=True).start()

        #Management with MQTT of Arduino's actuators and sensors
        self.broker = "broker.hivemq.com" 
        self.port = 1883
        self.tempTopic = "/tiot/group6/temperature"
        self.ledTopic = "/tiot/group6/led"
        self.motionTopic = "/tiot/group6/motion"
        self.alertTopic="/tiot/group6/alert"
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="SmartHomeEventController")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        try:
            self.mqtt_client.connect(self.broker, self.port, 60)
            self.mqtt_client.loop_start()
            print(f"MQTT Connected to {self.broker}:{self.port}\n")
        except Exception as e:
            print(f"MQTT Not Connected {e}\n")

    def PUT(self, *path, **query): #REST method to update the configurable threshold
        body= cherrypy.request.body.read()
        bodyDict=json.loads(body)
        self.configurable_threshold = bodyDict["e"][0]["v"] #The threshold must be sent in an SenML
        print(f"Threshold updated to {self.configurable_threshold}°C")
        return json.dumps({"threshold": self.configurable_threshold}).encode()


    def GET(self, *path, **query):
        return json.dumps({
            "rooms": self.roomsReadings,
            "statistics": self.roomStatistics,
            "threshold": self.configurable_threshold
        }, default=str).encode()
 


    def refreshRegistration_loop(self):
        while(True):
            time.sleep(60) #Every 60 seconds sends an update for the registration on the catalog
            try:
                requests.put(catalog_url, json=self.body)
                self.time=time.time()
            except Exception as e:
                print("Error in Refreshing the catalog registration")


    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker.")
            self.mqtt_client.subscribe(self.tempTopic)
            self.mqtt_client.subscribe(self.motionTopic)
            print("Subscribed to Arduino Sensors Topics.")
        else:
            print(f"Failed to connect to MQTT broker, return code {rc}\n")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            sensor_data = json.loads(payload)
            room = sensor_data["bn"]

            if room not in self.roomsReadings:
                self.roomsReadings[room] = {
                    "temperatures": [],
                    "lastMotionTime": None 
                }
                self.roomStatistics[room] = {"min": 0, "max": 0, "avg": 0}

            if msg.topic.endswith("temperature"):
                self.newTemperatureReading(sensor_data)
            elif msg.topic.endswith("motion"):
                self.motionSensorReading(sensor_data)
 
            print(f"MQTT Received [{msg.topic}] presence={self.checkPresence(room)}")
 
        except Exception as e:
            print(f"MQTT Error: {e}")


    def motionSensorReading(self, data):
        room=data["bn"] #The room is the basename of the SenML
        val = data["e"][0]["v"]

        if val == 1 or val == True:
            self.roomsReadings[room]["lastMotionTime"] = time.time()
            print(f"Motion detected in {room}, presence timer reset")
        if len(self.roomsReadings[room]["temperatures"]) > 0:
            self.valuateCommands(room, self.roomsReadings[room]["temperatures"][-1])

    def checkPresence(self, room):
        lastMotion = self.roomsReadings[room]["lastMotionTime"]
        if lastMotion is None:
            return False
        return (time.time() - lastMotion) <= TIMEOUT_PIR

    
    def newTemperatureReading(self, data): 
        val = data["e"][0]["v"]
        if val > ALERT_THRESHOLD: #Condition in case the maximum threshlod have been surpassed
            payload={"description":"Exceeded the maximim accepted temperature"}
            self.mqtt_client.publish(self.alertTopic, json.dumps(payload))

        room=data["bn"] #The room is the basename of the SenML
        self.updateStatistics(room, val)
        self.valuateCommands(room, val)
    
    def updateStatistics(self, room, newTemp):
        temps = self.roomsReadings[room]["temperatures"]
        if len(temps) < 10: #When the list has less tha 10 elements
            temps.append(newTemp)
        else:
            temps.pop(0)
            temps.append(newTemp)
        
        #Computing the statistics with the new element of the list
        self.roomStatistics[room]["max"]= max(temps)
        self.roomStatistics[room]["min"]= min(temps)
        self.roomStatistics[room]["avg"]= sum(temps)/len(temps)
        print(f"Stats [{room}]: min={self.roomStatistics[room]['min']:.1f} "
              f"max={self.roomStatistics[room]['max']:.1f} "
              f"avg={self.roomStatistics[room]['avg']:.1f}")

    
    def valuateCommands(self, room, lastVal):
        presence = self.checkPresence(room)
        payload = {"bn": room, "e": [{"n": "led", "v": False, "u": "boolean", "t": time.time()}]}
        if presence:
            if lastVal >= self.configurable_threshold:
                #yes presence no led
                self.mqtt_client.publish(self.ledTopic, json.dumps(payload))
                print(f"[{room}] Presence=True, T={lastVal:.1f}>={self.configurable_threshold} → LED OFF")
            else:
                #yes presence yes led
                payload["e"][0]["v"] = True
                self.mqtt_client.publish(self.ledTopic, json.dumps(payload))
                print(f"[{room}] Presence=True, T={lastVal:.1f}<{self.configurable_threshold} → LED ON")
        else:
            #No presence No led
            self.mqtt_client.publish(self.ledTopic, json.dumps(payload))
            print(f"[{room}] Presence=False → LED OFF")


if __name__ == '__main__':
    conf = {'/': {
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Content-Type', 'application/json')]
    }}
    cherrypy.tree.mount(SmartHomeController(), '/', conf)
    cherrypy.config.update({'server.socket_port': 9091})
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.engine.start()
    cherrypy.engine.block()
