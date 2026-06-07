#Software Laboratory Part 1, Includes Exercise 1, 2, 3 and 4

import time
import random

import cherrypy
import json

class room():
    def __init__(self, name):
        self.sens=dict()
        self.act=dict()
        self.act["thermostat"]=list()
        self.act["lights"]=list()
        self.act["blinds"]=list()
        self.actUnits=["°C", "%", "boolean"]
        self.name= name
    
    def getName(self):
        return self.name
    
    def getSens(self):
        self.sens["temperature"]=(random.uniform(10, 30), "°C")
        self.sens["humidity"]=(random.randint(25, 100), "%")
        self.sens["motion"]=(random.choice([True, False]),"boolean")
        return self.sens

    def setAct(self, name, val):
        self.act[name].append(val)

    def getActs(self):
        return self.act
    

class SmartHomeService(object):
    exposed=True
    def __init__(self):
        self.roomNames=["livingroom", "kitchen", "bedroom"]
        self.sens=["temperature", "humidity", "motion"]
        self.actuators=["thermostat", "lights", "blinds"]
        self.actsUnits={"thermostat":"°C", "lights":"boolean", "blinds":"%"}
        self.rooms=dict()
        self.salotto = room(self.roomNames[0])
        self.cucina = room(self.roomNames[1])
        self.camera = room(self.roomNames[2])
        self.rooms[self.roomNames[0]]=self.salotto
        self.rooms[self.roomNames[1]]=self.cucina
        self.rooms[self.roomNames[2]]=self.camera
        self.eventLogger= EventLog()

    def GET(self, *path, **query):
        if not path:
            raise cherrypy.HTTPError(400, "Missing path")
        
        if(path[0] == "sensors"):
            match len(path):
                case 1:
                    dTot=list()
                    for camera in self.roomNames:
                        d=dict()
                        d["bn"]= str(path[0]+"/"+camera)
                        d["e"]=list()
                        for sensori in self.sens: 
                            d2=dict()
                            d2["t"]= time.time()
                            d2["n"]= sensori
                            d2["u"]= self.rooms[camera].getSens().get(sensori)[1]
                            d2["v"]= self.rooms[camera].getSens().get(sensori)[0]
                            d["e"].append(d2)
                        
                        self.eventLogger.postEvent(d)
                        dTot.append(d)
                    return json.dumps(dTot).encode()
                case 2:
                    dTot=list()
                    if(path[1] in self.roomNames):
                        d=dict()
                        d["bn"]= str(path[0]+"/"+path[1])
                        d["e"]=list()
                        for sensori in self.sens: 
                            d2=dict()
                            d2["t"]= time.time()
                            d2["n"]= sensori
                            d2["u"]= self.rooms[path[1]].getSens().get(sensori)[1]
                            d2["v"]= self.rooms[path[1]].getSens().get(sensori)[0]
                            d["e"].append(d2)
                        self.eventLogger.postEvent(d)
                        dTot.append(d)
                        return json.dumps(dTot).encode()
                    else:
                        raise cherrypy.HTTPError(404, "Room not Existing")
                case 3:
                    if(path[1] in self.roomNames):
                        if(path[2] in self.sens):
                            d=dict()
                            d["bn"]= str(path[0]+"/"+path[1]+"/"+path[2])
                            d2=dict()
                            d2["t"]= time.time()
                            d2["n"]= path[2]
                            d2["u"]= self.rooms[path[1]].getSens().get(path[2])[1]
                            d2["v"]= self.rooms[path[1]].getSens().get(path[2])[0]
                            d['e']=d2
                            self.eventLogger.postEvent(d)
                            return json.dumps(d).encode()
                        else:
                            raise cherrypy.HTTPError(400, "Sensor not existing")
                    else:
                        raise cherrypy.HTTPError(404, "Room not Existing")
        elif(path[0] == "actuators"):
            match len(path):
                case 1:
                    dTot= self._generate_tot(path)
                    return json.dumps(dTot).encode()
                case 2:
                    dTot=list()
                    if(path[1] in self.roomNames):
                        d= self._generate_room(path,path[1])
                        self.eventLogger.postEvent(d)
                        dTot.append(d)
                        return json.dumps(dTot).encode()
                    else:
                        raise cherrypy.HTTPError(404, "Room not Existing")
                case 3:
                    if(path[1] in self.roomNames):
                        if(path[2] in self.actuators):
                            d=dict()
                            d["bn"]= str(path[0]+"/"+path[1]+"/"+path[2])
                            d["e"] = self._generate_actuator(path, path[1], path[2])
                            self.eventLogger.postEvent(d)
                            return json.dumps(d).encode()
                        else:
                            raise cherrypy.HTTPError(400, "Actuator not existing")
                    else:
                        raise cherrypy.HTTPError(404, "Room not Existing")
        else:
             raise cherrypy.HTTPError(400, "Wrong source, you have to use sensors or actuators")
    




    def _generate_tot(self,path):
        dTot=list()
        for camera in self.roomNames:
            d= self._generate_room(self,path,camera)
            dTot.append(d)
        return dTot


    def _generate_room(self,path,room):
        d=dict()
        d["bn"]= str(path[0]+"/"+room)
        d["e"]=list()
        for attuatori in self.actuators: 
            d2 = self._generate_actuator(self,path,room,attuatori)
            d["e"].append(d2)
        return d

    def _generate_actuator(self,path,room,actuator):
        d2=dict()
        d2["t"]= time.time()
        d2["n"]= actuator
        if(len(self.rooms[room].getActs().get(actuator)) >0):
            d2["u"]= self.actsUnits[actuator]
            d2["v"]= self.rooms[room].getActs().get(actuator)[-1]
        return d2

    def POST(self, *path, **query):
        if(len(path)>0 and path[0] == "actuators"):
            if(path[1] in self.roomNames):
                body= cherrypy.request.body.read()
                bodyDictGeneral=json.loads(body)
                if("e" not in bodyDictGeneral.keys() or "bn" not in bodyDictGeneral.keys()):
                    raise cherrypy.HTTPError(422, "Unprocessable Entity")
                
                bodyDict=bodyDictGeneral["e"]
                chiavi=bodyDict.keys()

                if("n" not in chiavi or "v" not in chiavi or "u" not in chiavi or "t" not in chiavi):
                    raise cherrypy.HTTPError(422, "Unprocessable Entity")
                
                if(bodyDict["n"] in self.actuators):
                    if(bodyDict["n"] == "thermostat" and (bodyDict["v"] < 10 or bodyDict["v"] > 30) and bodyDict["u"] == "°C"):
                        raise cherrypy.HTTPError(400, "Values out of Range, thermostat between 10 and 30 °C")
                    
                    if(bodyDict["n"] == "lights" and (bodyDict["v"] != "on" and bodyDict["v"] != "off") and bodyDict["u"] == "boolean"):
                        raise cherrypy.HTTPError(400, "Values out of Range, lights only on and off")
                    
                    if(bodyDict["n"] == "blinds" and (bodyDict["v"] < 0 or bodyDict["v"] > 100) and bodyDict["u"] == "%"):
                        raise cherrypy.HTTPError(400, "Values out of Range, blinds only between 0 and 100")
                    
                    if(bodyDict["n"] == "led" and (bodyDict["v"] != "on" and bodyDict["v"] != "off") and bodyDict["u"] == "boolean"):
                        raise cherrypy.HTTPError(400, "Values out of Range, lights only on and off")
                    
                    self.eventLogger.postEvent(bodyDictGeneral)
                    self.rooms[path[1]].setAct(bodyDict["n"], bodyDict["v"])
                else:
                    raise cherrypy.HTTPError(404, "Unknown device")
            else:
                raise cherrypy.HTTPError(404, "Room not Existing")
            
class EventLog(object):
    exposed=True
    def __init__(self):
        self.events=list()
        self.roomNames=["livingroom", "kitchen", "bedroom"]
        self.sens=["temperature", "humidity", "motion"]
    
    def GET(self, *path, **query):
        match len(path):
            case 1:
                    if(len(query) > 0 and ("room" in query.keys() ) and ("since" in query.keys())):
                        res=dict()
                        for e in self.events:
                            if((query["room"] in e["bn"] ) and (e["e"]["t"]>= query["since"])):
                                res.append(e)
                        return json.dumps(res).encode()
                    else:
                        return json.dumps(self.events).encode()
            case 2:
               if(path[1] in self.roomNames and path[0] == "log" ):
                    res=dict()
                    for e in self.events:
                        if(path[1] in e["bn"]):
                            res.append(e)
                    return json.dumps(res).encode()

    def postEvent(self, body):
        self.events.append(body)
        return

    def POST(self, *path, **query):
        body= cherrypy.request.body.read().decode('utf-8')
        bodyDict= json.loads(body.strip())
        self.events.append(bodyDict)
        return

    def DELETE(self, *path, **query):
        if(len(path)> 0 and path[0]== "log" and "before" in query.keys()):
            time=query["before"]
            indice=0
            count=0
            newList=list()
            for e in self.events:
                if(e["t"]< time):
                    indice +=1
                    count+=1
                else:
                    newList.append(e)
            self.events=newList
            return count
        
if __name__ == '__main__':
    conf = {
        '/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on': True,
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Content-Type', 'application/json')]} 
        }
    
    cherrypy.tree.mount(SmartHomeService (), '/', conf)
    cherrypy.tree.mount(EventLog (), '/log', conf)
    cherrypy.config.update({'server.socket_host': '10.24.110.101'})
    cherrypy.config.update({'server.socket_port': 9090})
    cherrypy.engine.start()
    cherrypy.engine.block()