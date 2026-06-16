#Class of Software Laboratory Part 1
from objects import *

class SmartHome(object):
    def __init__(self,eventLog,catalog):
        self.eventLog = eventLog
        self.catalog = catalog
        self.rooms = dict()
        self.rooms["kitchen"] = Room("Kitchen")
        self.rooms["living_room"] = Room("Living Room")
        self.rooms["bedroom"] = Room("Bedroom")
