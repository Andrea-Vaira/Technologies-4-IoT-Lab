#Software Laboratpry Part 2, Exercise 5
import os
from threading import Lock
import json

DB_FILE = "catalog.json"

'''
Info:
    ID
    Description
    Rest endpoint URL
    MQTT info(ip,port,topic)
    Resources List
    timestamp
'''

class FileManager:
    def __init__(self):
        self.lock = Lock()
        self.data = {"devices": {}, "services": {}, "broker": {"ip":"localhost","port":1883}, "sID" : 0, "dID" : 0}
        self.load()

    def load(self):
        with self.lock:
            if os.path.exists(DB_FILE):
                try:
                    with open(DB_FILE, "r") as f:
                        self.data = json.load(f)
                        self.data["sID"] = 0
                        self.data["dID"] = 0
                except json.JSONDecodeError:
                    print("[Warning] Corrupted JSON file. Starting fresh.")
            else:
                self.save()

    def save(self):
        with open(DB_FILE, "w") as f:
            json.dump(self.data, f, indent=4)
    
    def read(self):
        info = dict()
        with self.lock:
            with open(DB_FILE, "r") as f:
                file=f.read()
                info=json.loads(file)
        return info
    
    def write(self, info):
        with self.lock:
            if("d" in info["ID"]):
                self.data["devices"][info["ID"]]= info
            elif("s" in info["ID"]):
                self.data["services"][info["ID"]]= info
            else:
                print("Error")
            self.save()
    
    def delete(self, id):
        with self.lock:
            if("d" in id):
                self.data["devices"].pop(id)
            elif("s" in id):
                self.data["services"].pop(id)
            else:
                print("Error")
            self.save()
