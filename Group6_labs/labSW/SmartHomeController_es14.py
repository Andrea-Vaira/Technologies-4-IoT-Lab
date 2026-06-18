#Software Laboratory Part 3, Exercise 14, Complete Controller communicating with the Arduino and the Catalog
import time
import json
import threading
import requests
import cherrypy
import paho.mqtt.client as mqtt

catalog_url = "http://localhost:8080/catalog" 

alert_threshold= 30 #Maximum temperature also used in the Arduino Lab 2.1
TIMEOUT_PIR_PRESENCE= 30*60 #Minimum time (30 minutes) to consider as empty a room from the PIR
TIMEOUT_MIC_PRESENCE= 60*60 #Minimum time (60 minutes) to consider as empty a room from the microphone

class SmartHomeController(object):
    exposed=True

    def __init__(self):
        self.roomsReadings={} #For each room there is a sub-dictionary with the readings
        self.num=0
        self.roomStatistics={}
        self.motionStatus=False
        self.configurable_threshold=26
        self.presenceFlag=False

        #Regitration over REST for the Catalog
        self.body={}
        self.body["ID"]= "Controller_s00000" 
        self.body["description"]="Service that controls the entire system"
        try:
            requests.post((catalog_url), json=self.body) #Registers to the catalog via REST using POST
        except Exception as e:
            print("Error, Not Registred in the Catalog")
        threading.Thread(target=self.refreshRegistration_loop, daemon=True).start()

        #Management with MQTT of Arduino's actuators and sensors
        self.broker = "broker.hivemq.com" 
        self.port = 1883
        self.tempTopic="/tiot/group6/+/temperature"
        self.ledTopic="/tiot/group6/{}/led"
        self.motionTopic= "/tiot/group6/+/motion"
        self.soundTopic= "/tiot/group6/+/sound"
        self.displayTopic="/tiot/group6/{}/display"
        self.fanTopic="/tiot/group6/{}/fan"
        self.alertTopic="/tiot/group6/alert"
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="SmartHomeEventController")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        threading.Thread(target=self.displayPrint_loop, daemon=True).start()

        try:
            self.mqtt_client.connect(self.broker, self.port, 60)
            self.mqtt_client.loop_start()
            print(f"MQTT Connected to {self.broker}:{self.port}\n")
        except Exception as e:
            print(f"MQTT Not Connected {e}\n")

    def PUT(self, *path, **query): #REST method to update the configurable threshold
        body= cherrypy.request.body.read()
        bodyDict=json.loads(body)
        self.configurable_threshold= bodyDict["e"][0]["v"] #The threshold must be sent in an SenML
        return

    def refreshRegistration_loop(self):
        while(True):
            time.sleep(60) #Every 60 seconds sends an update for the registration on the catalog
            try:
                response = requests.put(catalog_url, json=self.body)
                self.time=time.time()
                if response.status_code == 404 or "not in the catalog" in response.text.lower():
                    print("Controller rimosso dal catalogo. Tento nuova registrazione (POST)...")
                    requests.post(catalog_url, json=self.body)
            except Exception as e:
                print("Error in Refreshing the catalog registration")


    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker.")
            self.mqtt_client.subscribe(self.tempTopic)
            self.mqtt_client.subscribe(self.motionTopic)
            self.mqtt_client.subscribe(self.soundTopic)
            self.mqtt_client.subscribe("/tiot/ArduinoGroup6/settings")
            print("Subscribed to Arduino Sensors Topics.")
        else:
            print(f"Failed to connect to MQTT broker, return code {rc}\n")
        return
    

    def on_message(self, client, userdata, msg):
        if msg.topic == "/tiot/ArduinoGroup6/settings":
            try:
                command = msg.payload.decode('utf-8')
                if command.startswith("SET:"):
                    params = command.replace("SET:", "").split(",")
                    if len(params) == 4:     
                        ac_min, ac_max = float(params[0]), float(params[1])
                        ht_min, ht_max = float(params[2]), float(params[3])
                        self.valAC = (ac_min, ac_max)
                        self.valHeat = (ht_min, ht_max)
                        print(f"Set-points updated -> AC:[{ac_min},{ac_max}] HT:[{ht_min},{ht_max}]")
            except Exception as e:
                print(f"Errore in the Serial Parsing: {e}")
            return
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            if not isinstance(payload, dict):
                return
            room = payload.get("bn", "default_room")
            
            if room not in self.roomsReadings:
                self.roomsReadings[room] = {
                    "temperatures": [], "presence": False, 
                    "last_motion": 0, "sound_events": []
                }

            current_server_time = time.time()
        
            for event in payload.get("e", []):
                name = event.get("n")
                value = event.get("v")
            
                if name == "temperature":
                    self.roomsReadings[room]["temperatures"].append(value)
                    if len(self.roomsReadings[room]["temperatures"]) > 10:
                        self.roomsReadings[room]["temperatures"].pop(0)
                        
                elif name == "motion" and value == True:
                    self.roomsReadings[room]["last_motion"] = current_server_time
                    
                elif name == "sound" and value == True:
                    self.roomsReadings[room]["sound_events"].append(current_server_time)
                
                
            self.evaluate_presence_and_controls(room)
            print(f"MQTT Received and processed for room: {room}")
        except json.JSONDecodeError as e:
            print(f"Only JSON packets: {e}")
        except Exception as e:
            print(f"MQTT Error: {e}")

    def evaluate_presence_and_controls(self, room):
        now = time.time()
        readings = self.roomsReadings[room]
        
        readings["sound_events"] = [t for t in readings["sound_events"] if (now - t) <= 10*60]
        
        pir_presence = (now - readings["last_motion"]) <= 30*60
        
        mic_presence = len(readings["sound_events"]) >= 10

        presence = pir_presence or mic_presence
        readings["presence"] = presence

        lastVal = self.roomsReadings[room]["temperatures"][-1]
    
        if self.roomsReadings[room]["presence"] == True:
            valHeat=(15, 20)
            valCond=(25, 30)
        else: #Empty room
            valHeat=(10, 15)
            valCond=(27, 32)

        if lastVal < valCond[0]:
            fanSpeed = 0
        elif lastVal > valCond[1]:
            fanSpeed = 100
        else:
            fanSpeed = int(((lastVal - valCond[0]) / (valCond[1] - valCond[0])) * 100)

        if lastVal < valHeat[0]:
            ledBrightness = 0
        elif lastVal > valHeat[1]:
            ledBrightness = 100
        else:
            ledBrightness= int(((lastVal - valHeat[0]) / (valHeat[1] - valHeat[0])) * 100)
        
        readings["fan_speed"] = fanSpeed 
        readings["led_brightness"] = ledBrightness
        

    def soundSensorReading(self, data):
        room=data["bn"] #The room is the basename of the SenML
        val=data["e"][0]["v"]
        if val == 1:
            self.roomsReadings[room]["sound"].append(time.time())
        self.checkPresence(room)

    def motionSensorReading(self, data):
        room=data["bn"] #The room is the basename of the SenML
        val=data["e"][0]["v"]
        if str(val) == 1 or val == True or val == 1:
            self.roomsReadings[room]["motion"]= time.time()
        self.checkPresence(room)


    def checkPresence(self, room):
        now= time.time()
        if(self.roomsReadings[room]["motion"] != None):
            if((now - self.roomsReadings[room]["motion"]) > TIMEOUT_PIR_PRESENCE):
                presencePir= False
            else:
                presencePir=True
        else:
            presencePir=False
        
        indexes= list()
        for i, tSound in enumerate(self.roomsReadings[room]["sound"]):
            if((now- tSound) > 10*60): #If the sound was heard more than 10 minutes ago
                indexes.append(i)

        for i in sorted(indexes, reverse=True):
            del self.roomsReadings[room]["sound"][i]

        if(len(self.roomsReadings[room]["sound"]) <= 10):
            presenceMic=False
        elif((now-self.roomsReadings[room]["sound"][-1]) > TIMEOUT_MIC_PRESENCE):
            presenceMic=False
        else:
            presenceMic=True

        if(presenceMic or presencePir):
            self.roomsReadings[room]["presence"]= True
        else:
            self.roomsReadings[room]["presence"]= False
        
        if len(self.roomsReadings[room]["temperatures"]) > 0:
            self.valuateCommands(room, self.roomsReadings[room]["temperatures"][-1])
    
    def newTemperatureReading(self, data): 
        val=data["e"][0]["v"]
        room=data["bn"] #The room is the basename of the SenML
        if val > alert_threshold: #Condition in case the maximum threshlod have been surpassed
            payload={"description":"Exceeded the maximim accepted temperature"}
            self.mqtt_client.publish(self.alertTopic, json.dumps(payload))

        self.updateStatistics(room, val)
        self.valuateCommands(room, val)
    
    def updateStatistics(self, room, newTemp):
        temp = self.roomsReadings[room]["temperatures"]
        if len(temp) < 10: #When the list has less tha 10 elements
            temp.append(newTemp)
        else:
            temp.pop(0)
            temp.append(newTemp)
        
        #Computing the statistics with the new element of the list
        self.roomStatistics[room]["max"]= max(temp)
        self.roomStatistics[room]["min"]= min(temp)
        self.roomStatistics[room]["avg"]= sum(temp)/len(temp)
    
    def valuateCommands(self, room, lastVal):

        if self.roomsReadings[room]["presence"] == True:
            valHeat=(15, 20)
            valCond=(25, 30)
        else: #Empty room
            valHeat=(10, 15)
            valCond=(27, 32)

        #Executes the map the previously was done by Arduino
        if lastVal < valCond[0]:
            fanSpeed = 0
        elif lastVal > valCond[1]:
            fanSpeed = 100
        else:
            fanSpeed = int(((lastVal - valCond[0]) / (valCond[1] - valCond[0])) * 100)

        if lastVal < valHeat[0]:
            ledBrightness = 0
        elif lastVal > valHeat[1]:
            ledBrightness = 100
        else:
            ledBrightness= int(((lastVal - valHeat[0]) / (valHeat[1] - valHeat[0])) * 100)

        payloadLed= {"bn":room, "e":[{"n":"led", "v":ledBrightness, "u":"percentage", "t":time.time()}]}
        payloadFan= {"bn":room, "e":[{"n":"fan", "v":fanSpeed, "u":"percentage", "t":time.time()}]}
        
        self.mqtt_client.publish(self.ledTopic.format(room), json.dumps(payloadLed))
        self.mqtt_client.publish(self.fanTopic.format(room), json.dumps(payloadFan))
        
    def displayPrint_loop(self):
        screen_index = 0
        while True:
            for room in list(self.roomsReadings.keys()):
                readings = self.roomsReadings[room]
                if len(readings["temperatures"]) > 0:
                    temp = readings["temperatures"][-1]
                    presence = "SI" if readings.get("presence", False) else "NO"
                    fan = readings.get("fan_speed", 0)
                    heat = readings.get("led_brightness", 0)
                    
                    ac_min, ac_max = self.valAC if hasattr(self, 'valAC') else (25, 30)
                    ht_min, ht_max = self.valHeat if hasattr(self, 'valHeat') else (20, 15)
                    
                    if screen_index == 0:
                        text = f"T:{temp}C Pres:{presence}"
                    elif screen_index == 1:
                        text = f"V:{fan}% Risc:{heat}%"
                    else:
                        text = f"AC:{ac_min}-{ac_max} H:{ht_max}-{ht_min}"
                    
                    payload = {"bn": room, "e": [{"n": "display", "v": text, "u": "string", "t": time.time()}]}
                    self.mqtt_client.publish(self.displayTopic.format(room), json.dumps(payload))
                    
            screen_index = (screen_index + 1) % 3
            time.sleep(5)

if __name__ == '__main__':
    conf = {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                  'tools.response_headers.on': True,
                  'tools.response_headers.headers': [('Content-Type', 'application/json')]}}
    cherrypy.tree.mount(SmartHomeController(), '/', conf)
    cherrypy.config.update({'server.socket_port': 9091})
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.engine.start()
    cherrypy.engine.block()