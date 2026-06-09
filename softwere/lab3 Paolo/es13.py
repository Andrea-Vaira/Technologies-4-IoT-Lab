#Software Laboratory Part 3, Exercise 13
import time
import json
import threading
import requests
import cherrypy
import paho.mqtt.client as mqtt

catalog_url= "http://localhost:8080" #Da definire

class SmartHomeController(object):
    exposed=True

    def __init__(self):
        #Regitration over REST for the Catalog
        self.time= time.time()
        self.body={}
        '''Necessario un modo per assegnare un ID senza passare dal Catalog Client per usare REST, Se facessimo
        partire il conteggio degli id da 1 sul FileManager/Catalog, potremmo assegnare al Controllore s00000 direttamente.'''
        self.body["ID"]= "s00000" 
        self.body["description"]="Service that controls the entire system"
        self.body["timestamp"]=self.time
        try:
            requests.post((catalog_url+"/registration"), data=self.body) #Registers to the catalog via REST using POST
        except Exception as e:
            print("Error, Not Registred in the Catalog")
        threading.Thread(target=self.refreshRegistration_loop, daemon=True).start()

        #Management with MQTT of Arduino's actuators and sensors
        self.broker = "broker.hivemq.com" 
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


    def refreshRegistration_loop(self):
        while(True):
            now=time.time()
            if((now - self.time)> 60): #Every 60 seconds sends an update for the registration on the catalog
                requests.put(catalog_url+"/registration", data=self.body)
                self.time=time.time()


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

if __name__ == '__main__':
    conf = {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                  'tools.response_headers.on': True,
                  'tools.response_headers.headers': [('Content-Type', 'application/json')]}}
    cherrypy.tree.mount(SmartHomeController(), '/', conf)
    cherrypy.config.update({'server.socket_port': 9090})
    cherrypy.engine.start()
    cherrypy.engine.block()