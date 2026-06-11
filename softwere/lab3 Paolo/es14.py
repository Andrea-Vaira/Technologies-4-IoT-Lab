#Software Laboratory Part 3, Exercise 14, Complete Controller communicating with the Arduino and the Catalog
import time
import json
import threading
import requests
import cherrypy
import paho.mqtt.client as mqtt

catalog_url= "http://xx.xx.xx.xx:9090" #To be defined

alert_threshold= 30 #Maximum temperature also used in the Arduino Lab 2.1

class SmartHomeController(object):
    exposed=True

    def __init__(self):
        self.roomsReadings={} #List with the 10 last readings
        self.num=0
        self.roomStatistics={}
        self.motionStatus=False
        self.configurable_threshold=26

        #Regitration over REST for the Catalog
        self.body={}
        '''Necessario un modo per assegnare un ID senza passare dal Catalog Client per usare REST, Se facessimo
        partire il conteggio degli id da 1 sul FileManager/Catalog, potremmo assegnare al Controllore s00000 direttamente.'''
        self.body["ID"]= "s00000" 
        self.body["description"]="Service that controls the entire system"
        try:
            requests.post((catalog_url+"/registration"), json=self.body) #Registers to the catalog via REST using POST
        except Exception as e:
            print("Error, Not Registred in the Catalog")
        threading.Thread(target=self.refreshRegistration_loop, daemon=True).start()

        #Management with MQTT of Arduino's actuators and sensors
        self.broker = "broker.hivemq.com" 
        self.port = 1883
        self.tempTopic="/tiot/group6/+/temperature"
        self.ledTopic="/tiot/group6/{}/led"
        self.motionTopic= "/tiot/group6/+/motion"
        self.displayTopic="/tiot/group6/{}/display"
        self.fanTopic="/tiot/group6/{}/fan"
        self.alertTopic="/tiot/group6/alert"
        self.mqtt_client = mqtt.Client(client_id="SmartHomeEventController")
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
        self.configurable_threshold= bodyDict["v"] #The threshold must be sent in an SenML
        return

    def refreshRegistration_loop(self):
        while(True):
            time.sleep(60) #Every 60 seconds sends an update for the registration on the catalog
            try:
                requests.put(catalog_url+"/registration", json=self.body)
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

            if sensor_data["bn"] not in self.roomsReadings.keys():
                    self.roomsReadings[sensor_data["bn"]]={"temperatures":list(), "motionStatus":False}
                    self.roomStatistics[sensor_data["bn"]]={"min":0, "max":0, "avg":0}
            
            if msg.topic.endswith("temperature"):
                self.newTemperatureReading(sensor_data)
            else:
                self.motionSensorReading(sensor_data)
            print("MQTT Received")

        except Exception as e:
            print(f"MQTT Error: {e}")

    def motionSensorReading(self, data):
        room=data["bn"] #The room is the basename of the SenML
        val=data["v"]
        self.roomsReadings[room]["motionStatus"]= val
        if len(self.roomsReadings[room]["temperatures"]) > 0:
            self.valuateCommands(room, self.roomsReadings[room]["temperatures"][-1])
    
    def newTemperatureReading(self, data): 
        val=data["v"]
        if val > alert_threshold: #Condition in case the maximum threshlod have been surpassed
            payload={"description":"Exceeded the maximim accepted temperature"}
            self.mqtt_client.publish(self.alertTopic, json.dumps(payload))

        room=data["bn"] #The room is the basename of the SenML
        self.updateStatistics(room, val)
        self.valuateCommands(room, val)
    
    def updateStatistics(self, room, newTemp):
        if len(self.roomsReadings[room]["temperatures"]) < 10: #When the list has less tha 10 elements
            self.roomsReadings[room]["temperatures"].append(newTemp)
        else:
            self.roomsReadings[room]["temperatures"].pop(0)
            self.roomsReadings[room]["temperatures"].append(newTemp)
        
        #Computing the statistics with the new element of the list
        self.roomStatistics[room]["max"]= max(self.roomsReadings[room]["temperatures"])
        self.roomStatistics[room]["min"]= min(self.roomsReadings[room]["temperatures"])
        self.roomStatistics[room]["avg"]= sum(self.roomsReadings[room]["temperatures"])/len(self.roomsReadings[room]["temperatures"])
    
    def valuateCommands(self, room, lastVal):
        payload= {"bn":room, "n":"led", "v":"off", "u":"boolean", "t":time.time()}
        if self.roomsReadings[room]["motionStatus"]== True:
            if lastVal >= self.configurable_threshold:
                self.mqtt_client.publish(self.ledTopic.format(room), json.dumps(payload))
            else:
                payload["v"]="on" #Switch On the LED
                self.mqtt_client.publish(self.ledTopic.format(room), json.dumps(payload))
        else:
            self.mqtt_client.publish(self.ledTopic.format(room), json.dumps(payload))


if __name__ == '__main__':
    conf = {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                  'tools.response_headers.on': True,
                  'tools.response_headers.headers': [('Content-Type', 'application/json')]}}
    cherrypy.tree.mount(SmartHomeController(), '/', conf)
    cherrypy.config.update({'server.socket_port': 9090})
    cherrypy.engine.start()
    cherrypy.engine.block()