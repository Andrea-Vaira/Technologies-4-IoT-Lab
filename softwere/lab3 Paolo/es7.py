#Classes of Software Laboratory Part 2
import os
from threading import Lock
import threading
import time
import json
import cherrypy
import paho.mqtt.client as mqtt

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

    def __init__(self):
        threading.Thread(target=self._cleanup_loop, daemon=True).start()
        self.fm= FileManager()
        self.cat= dict()
        self.initializeCatalog()
        #Mqtt configuration
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.connection_menager
        self.mqtt_client.on_message = self.message_menager

        broker_info = self.fm.data.get("broker",{"ip": "localhost","port" : 1883})
        try:
            self.mqtt_client.connect(broker_info["ip"],broker_info["port"],60)
            self.mqtt_client.loop_start()
            print("MQTT CONNECTED")
        except Exception as e:
            print(f"MQTT Connection error :{e}")




    def initializeCatalog(self):
        for device in self.fm.data.get("devices", {}).values():
            self.cat[device["ID"]] = device.copy()

        for service in self.fm.data.get("services", {}).values():
            self.cat[service["ID"]] = service.copy()
        
    def _cleanup_loop(self):
        while True:
            toDelete = list()
            now = time.time()
            for id,body in list(self.cat.items()):
                if(now - body["timestamp"] > 120):
                    toDelete.append(id) 
            for id in toDelete:
                self.cat.pop(id)
                self.fm.delete(id)

            time.sleep(60)

    def getFileManager(self):
        return self.fm
    

    def connection_menager(self,client,userdata,flags,rc):
        print(f"MQTT connect with code {rc}")
        #wildcar +  becouse we can have devices or services
        client.subscribe("catalog/update/+")

    def message_menager(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            body = json.loads(payload)

            id_item = body.get("ID")
            if not id_item:
                return

            print(f"Update for item with ID : {id_item}")
            if id_item in self.cat.keys():
                self.update(id_item)
            else:
                self.add(body)

        except Exception as e:
            print(f"MQTT error : {e}")


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
            self.update(bodyDict["ID"])                      
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
        id = f"d{self.fm.data['dID']:06}"
        self.fm.data["dID"] += 1
        return id

    def getServiceID(self):
        id = f"d{self.fm.data['sID']:06}"
        self.fm.data["sID"] += 1
        return id
    
if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.quickstart(Catalog(), '/', conf)

