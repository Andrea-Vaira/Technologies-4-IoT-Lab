import os
from threading import Lock
import threading
import time
import random
import json
import cherrypy

DB_FILE = "catalog.json"
base_topic = "/tiot/group6"; 


class FileManager:
    def _init_(self):
        self.lock = Lock()
        self.data = {"devices": {}, "services": {}, "broker": {"ip":"localhost","port":1883}}
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
        info= dict()
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
    
    def delete(self, info):
        with self.lock:
            if("d" in info["ID"]):
                self.data["devices"].pop(info["ID"])
            elif("s" in info["ID"]):
                self.data["services"].pop(info["ID"])
            else:
                print("Error")
            self.save()

class Catalog(object):
    exposed=True

    def __init__(self):
        threading.Thread(target=self._cleanup_loop, daemon=True).start()
        self.fm= FileManager
        self.IDs= list()
        self.cat=list()

    def getFileManager(self):
        return self.fm
    
    def GET(self, *path, **query):
        data=self.fm.read()
        return json.dumps(data).encode()

    def POST(self, *path, **query):
        body= cherrypy.request.body.read().decode('utf-8')
        bodyDict= json.loads(body.strip())
        if(bodyDict["ID"] in self.IDs):
            for e in self.cat:
                if(e["ID"] == bodyDict["ID"]):
                    e["timestamp"] = time.time()
                    self.fm.update(e)
        else:
            self.IDs.append(bodyDict["ID"])
            self.cat.append(bodyDict)
            self.fm.write(bodyDict)


    def PUT(self, *path, **query):
        body= cherrypy.request.body.read().decode('utf-8')
        bodyDict= json.loads(body.strip())
        if(bodyDict["ID"] in self.IDs):
            for e in self.cat:
                if(e["ID"] == bodyDict["ID"]):
                    e["timestamp"] = time.time()
                    self.fm.write(e)
        else:
            self.IDs.append(bodyDict["ID"])
            self.cat.append(bodyDict)
            self.fm.write(bodyDict)


    def DELETE(self, *path, **query):
        body= cherrypy.request.body.read().decode('utf-8')
        bodyDict= json.loads(body.strip())
        if(bodyDict["ID"] in self.IDs):
            for e in self.cat:
                if(e["ID"] == bodyDict["ID"]):
                    e["timestamp"] = time.time()
                    self.fm.write(e)
        else:
            print("Error")

class CatalogBridge:




if __name__ == '__main__':
    conf = {
        '/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on': True,
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Content-Type', 'application/json')]} 
        }
    
    
    cherrypy.tree.mount(Catalog (), '/', conf)
    cherrypy.config.update({'server.socket_host': '10.24.110.101'})
    cherrypy.config.update({'server.socket_port': 9090})
    cherrypy.engine.start()
    cherrypy.engine.block()