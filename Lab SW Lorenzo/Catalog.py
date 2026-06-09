#Class of Software Laboratory Part 2
import threading
from Filemanager import *
import time
import cherrypy

class Catalog(object):
    exposed=True

    def __init__(self):
        self.fm= FileManager()
        self.cat= dict()
        self.initializeCatalog()
        threading.Thread(target=self._cleanup_loop, daemon=True).start()

    def getCatalog(self):
        return self.cat
    
    def initializeCatalog(self):
        for id,body in self.fm.data["devices"].items():
            self.cat[id] = body.copy()

        for id,body in self.fm.data["services"].items():
            self.cat[id] = body.copy()
        
    def _cleanup_loop(self):
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
        self.fm.save()
        return id

    def getServiceID(self):
        id = f"s{self.fm.data['sID']:06}"
        self.fm.data["sID"] += 1
        self.fm.save()
        return id



class CatalogClient(object):
    exposed=True

    def __init__(self):
        self.catalog= Catalog()
        self.fm = self.catalog.getFileManager()

    def get_catalog(self):
        return self.catalog.getCatalog()

    def get_devices(self):
        return [body for id,body in self.get_catalog().items() if "d" in id]

    def get_device(self, id):
        if "d" in id:
            return self.get_catalog()[id]
        else:
            print("error, id given is not a device")

    def get_services(self):
        return [body for id,body in self.get_catalog().items() if "s" in id]

    def get_service(self, id):
        if "s" in id:
            return self.get_catalog()[id]
        else:
            print("error, id given is not a service")

    def get_broker(self):
        return self.fm.data["broker"]

    def register_device(self, payload):
        id = self.catalog.getDeviceID()
        payload["ID"] = id
        self.catalog.add(payload)

    def refresh_device(self, id):
        for body in self.get_devices():
            if body["ID"] == id:
                self.catalog.update(id)
                return
        print("Error, device not in the catalog")

    def register_service(self, payload):
        id = self.catalog.getServiceID()
        payload["ID"] = id
        self.catalog.add(payload)

    def refresh_service(self, id):
        for body in self.get_services():
            if body["ID"] == id:
                self.catalog.update(id);
                return
        print("Error, service not in the catalog")