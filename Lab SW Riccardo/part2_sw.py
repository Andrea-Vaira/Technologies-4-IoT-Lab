#Classes of Software Laboratory Part 2
import os
from threading import Lock
import threading
import time
import json
import cherrypy

DB_FILE = "catalog.json"

'''
Info:
    ID
    Descriptionx
    Rest endpoint URL
    MQTT info(ip,port,topic)
    Resources List
    Timestamp
'''

class FileManager:
    def init(self):
        self.lock = Lock()
        self.data = {"devices": {}, "services": {}, "broker": {"ip":"localhost","port":1883}, "sID" : 0, "dID" : 0}
        self.load()

    def load(self):
        with self.lock:
            if os.path.exists(DB_FILE):
                try:
                    with open(DB_FILE, "r") as f:
                        self.data = json.load(f)
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

class Catalog(object):
    exposed=True

    def _init_(self):
        threading.Thread(target=self._cleanup_loop, daemon=True).start()
        self.fm= FileManager
        self.cat= dict()
        self.initializeCatalog()

    def initializeCatalog(self):
        for device in self.fm.data["device"]:
            self.cat[device["ID"]] = device.copy()

        for service in self.fm.data["service"]:
            self.cat[service["ID"]] = service.copy()
        
    def _cleanup_loop(self):
        while True:
            toDelete = list()
            now = time.time()
            for id,body in self.cat.items():
                if(now - body["timestamp"] > 120):
                    toDelete.append(id) 
            for id in toDelete:
                self.cat.pop(id)
                self.fm.delete(id)

            time.sleep(60)

    def getFileManager(self):
        return self.fm
    
    def GET(self, *path, **query):
        data=self.fm.read()
        return json.dumps(data).encode()
    
    #Distinguish create and modify
    def POST(self, *path, **query):
        body= cherrypy.request.body.read().decode('utf-8')
        bodyDict= json.loads(body.strip())
        if(bodyDict["ID"] not in self.cat.keys()):
            self.add(bodyDict)                      
        else:
            print("Item already in the catalog")

    def PUT(self, *path, **query):
        body= cherrypy.request.body.read().decode('utf-8')
        bodyDict= json.loads(body.strip())
        if(bodyDict["ID"] in self.cat.keys()):
            self.modify(bodyDict["ID"])                      
        else:
            print("Item not in the catalog")
        
    def add(self,body):
        body["timestamp"] = time.time()
        self.cat[body["ID"]] = body
        self.fm.write(body)

    def update(self,id):
        body = self.cat[id].copy()
        body["timestamp"] = time.time()
        self.cat[id] = body
        self.fm.write(body)

    def DELETE(self, *path, **query):
        body= cherrypy.request.body.read().decode('utf-8')
        bodyDict= json.loads(body.strip())
        id = bodyDict["ID"]
        if(id in self.cat.keys()):
            self.cat.pop(id)
            self.fm.delete(id)
        else:
            print("Error")

    def getDeviceID(self):
        id = f"d{self.fm.data["dID"]:06}"
        self.fm.data["dID"] += 1
        return id

    def getServiceID(self):
        id = f"d{self.fm.data['sID']:06}"
        self.fm.data["sID"] += 1
        return id



class CatalogClient(object):
    exposed=True

    def init(self):
        self.catalog= Catalog
        self.fm=self.catalog.getFileManager()

    def get_catalog(self):
        return self.catalog.GET()

    def get_devices(self):
        info= self.fm.read()
        return info["devices"]

    def get_device(self, id):
        info= self.fm.read()
        return info["devices"][id]

    def get_broker(self):
        info= self.fm.read()
        return info["broker"]

    def register_device(self, payload):
        id = self.catalog.getDeviceID()
        payload["ID"] = id
        self.catalog.add(payload)

    def refresh_device(self, id):
        if(id in self.catalog.cat.keys()):
            self.catalog.update(id)
        else:
            print("Error, device not in the catalog")

    def register_service(self, payload):
        id = self.catalog.getServiceID()
        payload["ID"] = id
        self.catalog.add(payload)

    def refresh_service(self, id):
        if(id in self.catalog.cat.keys()):
            self.catalog.update(id)
        else:
            print("Error, service not in the catalog")