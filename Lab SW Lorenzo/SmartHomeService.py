#Class of Software Laboratory Part 1
import json
import time
import cherrypy
from threading import Thread

class SmartHomeService(object):
    def __init__(self,home):
        self.rooms = home.rooms
        self.eventLog = home.eventLog
        self.catalog = home.catalog


    def checkRoomPresence(self,room):
        if(room not in self.rooms.keys()):
                raise cherrypy.HTTPError(404,"Room not found in the system, rooms available: " 
                                        + ", ".join(room for room in self.rooms.keys()))

    def checkSensorPresence(self,room,sensor):
        if(sensor not in self.rooms[room].getSensors().keys()):
            raise cherrypy.HTTPError(400,"Sensor not found in the " + room + ", sensors available: " 
                                        + ", ".join(sensor for sensor in self.rooms[room].getSensors().keys()))
    
    def checkActuatorPresence(self,room,actuator):
        if(actuator not in self.rooms[room].getActuators().keys()):
            raise cherrypy.HTTPError(400,"Actuator not found in the " + room + ", actuators available: " 
                                        + ", ".join(actuator for actuator in self.rooms[room].getActuators().keys()))

    def refreshService(self, id):
        try:
            self.catalog.refresh_service(id)
            print(f"[INFO] Connection succeded for service {id}")
            time.sleep(60)
        except Exception as e:
            print(f"[WARNING] Connection error for service {id}, retry in 60 seconds")
            print("[INFO] Error: {e}")
            time.sleep(60)
        
'''
Info:
    ID
    Description
    Rest endpoint URL
    MQTT info(ip,port,topic)
    Resources List
    Timestamp
'''

class SmartHomeSensorService(SmartHomeService):
    exposed = True

    def __init__(self, home):
        super().__init__(home)
        self.info = {
            "ID" : -1,
            "description" : "Service that manages the sensor system",
            "rest" : "http://localhost:8080/sensor",
            "mqtt" : self.catalog.get_broker(),
            "resources" : "Boh",
            "timestamp" : -1
        }
        self.catalog.register_service(self.info)
        Thread(target=self.refreshService, args=(self.info["ID"],), daemon=True).start()
            
    def GET(self,*path,**query):
        roomN = query.get("room", "")
        n = query.get("sensor","")
        if(len(path) == 2):
            if(roomN != path[0] and roomN != ""):
                print("Query and path in conflict for the room, retry...")
                return
            if(n != path[1] and n != ""):
                print("Query and path in conflict for the sensor, retry...")
                return
            roomN = path[0]
            n = path[1]
            #check for errors
            self.checkRoomPresence(roomN)
            self.checkSensorPresence(roomN,n)

            #Retrieve sensor and measurement
            sensor = self.rooms[roomN].getSensor(n)
            event = self.senmlEventFromRead(sensor,sensor.getName())

            #sml to return
            finalSml = {
                'bn' : f'sensor/{roomN}/',
                'bt' : round(time.time()),
                'e' : [event]
            }
        elif(len(path) == 1):
            if(roomN != path[0] and roomN != ""):
                print("Query and path in conflict for the room, retry...")
                return
            roomN = path[0]
            #checks
            self.checkRoomPresence(roomN)

            #Create a list of events, one for each sensor reading
            events = list()
            for sensor in self.rooms[roomN].getSensors().values(): #accedo a tutti sensori nella stanza con nome=roomN
                events.append(self.senmlEventFromRead(sensor,sensor.getName()))

            #sml to return
            finalSml = {
                'bn' : f'sensor/{roomN}/',
                'bt' : round(time.time()),
                'e' : events
            }
        else:
            #no checks, create a list of events with resource name = room/sensor
            events = list()
            for room in self.rooms.values():
                for sensor in room.getSensors().values():
                    resName = f'{room.getName()}/{sensor.getName()}'
                    events.append(self.senmlEventFromRead(sensor,resName))

            #sml to return
            finalSml = {
                'bn' : f'sensor/',
                'bt' : round(time.time()),
                'e' : events
            }
        self.eventLog.add(finalSml)
        return json.dumps(finalSml).encode()
        
    def senmlEventFromRead(self,sensor,resName):
        sml = dict()
        sml["n"] = resName
        sml["u"] = sensor.getUnit()
        sml["v"] = sensor.read()
        return sml

class SmartHomeActuatorService(SmartHomeService):
    exposed = True

    def __init__(self, home):
        super().__init__(home)
        self.info = {
            "ID" : -1,
            "description" : "Service that manages the actuator system",
            "rest" : "http://localhost:8080/actuator",
            "mqtt" : self.catalog.get_broker(),
            "resources" : "Boh",
            "timestamp" : -1
        }
        self.catalog.register_service(self.info) 
        Thread(target=self.refreshService, args=(self.info["ID"],), daemon=True).start()

    def PUT(self,*path,**query):
        try: 
            request = json.loads(cherrypy.request.body.read())
            room = request["bn"].split("/")[1]
            actuatorName = request["e"][0]["n"]
            newState = request["e"][0]["v"]
            self.checkRoomPresence(room)
            self.checkActuatorPresence(room,actuatorName)
            self.rooms[room].getActuator(actuatorName).setState(newState)
            finalSml = {
                'bn' : f'actuator/{room}/',
                'bt' : round(time.time()),
                'e' : request["e"] 
            }
            self.eventLog.add(finalSml)
            return
        except ValueError:
            raise cherrypy.HTTPError(422,"Unprocessable entity: SenML body is malformed")
        
    def GET(self,*path,**query):
        roomN = path[0]
        n = path[1]
        #Controlli 
        self.checkRoomPresence(roomN)
        self.checkActuatorPresence(roomN,n)

        #Recupero l'attuatore ed eseguo la lettura
        actuator = self.rooms[roomN].getActuator(n)
        event = self.senmlEventFromRead(actuator,actuator.getName())

        #istanzio l'sml finale
        finalSml = {
            'bn' : f'actuator/{roomN}/',
            'bt' : round(time.time()),
            'e' : [event]
        }
        return json.dumps(finalSml).encode()

    def senmlEventFromRead(self,actuator,resName):
        sml = dict()
        sml["n"] = resName
        sml["u"] = actuator.getUnit()
        sml["v"] = actuator.getState()
        return sml


