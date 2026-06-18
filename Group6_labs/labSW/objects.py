#Software Laboratory Part 1, Classes for exercise from 1 to 4
import random

class Sensor(object):
    def __init__(self,name,unit,range):
        self.name = name
        self.unit = unit
        self.range = range
    
    def getName(self):
        return self.name
    
    def getUnit(self):
        return self.unit
    
    def read(self):
        return round(random.uniform(self.range[0],self.range[1]),0)

class Actuator(object):
    def __init__(self,name,unit,range,startState):
        self.name = name
        self.unit = unit
        self.range = range
        self.state = startState

    def getName(self):
        return self.name
    
    def getUnit(self):
        return self.unit
    
    def getState(self):
        return self.state
    
    def setState(self,state):
        self.state = state

    
class Room(object):
    def __init__(self,name):
        self.name = name

        sensors = dict()
        sensors["temperature"] = Sensor("temperature","Cel",(-10,40))
        sensors["humidity"] = Sensor("humidity","%RH",(0,100))
        sensors["motion"] = Sensor("motion","boolean",(0,1))
        actuators = dict()
        actuators["thermostat"] = Actuator("thermostat","cel",(10,30),20)
        actuators["lights"] = Actuator("lights","boolean",(0,1),0)
        actuators["blinds"] = Actuator("blinds","position %",(0,100),0)

    def getName(self):
            return self.name
            
    def getSensors(self):
        return self.sensors
    
    def getSensor(self,name):
        return self.sensors[name]
    
    def getActuators(self):
        return self.actuators
    
    def getActuator(self,name):
        return self.actuators[name]
    