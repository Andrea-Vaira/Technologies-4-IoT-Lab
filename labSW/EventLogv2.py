#Software Laboratory Part 3, Exercise 12
import json
import cherrypy
import paho.mqtt.client as mqtt


class EventLogv2(object):
    exposed=True
    def __init__(self):
        self.events=list()
        self.roomNames=["livingroom", "kitchen", "bedroom"]
        self.sens=["temperature", "humidity", "motion"]
        self.broker = "broker.hivemq.com"  
        self.port = 1883
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="SmartHomeEventLog_Sub")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        try:
            self.mqtt_client.connect(self.broker, self.port, 60)
            self.mqtt_client.loop_start()
            print(f"MQTT Connected to {self.broker}:{self.port}...")
        except Exception as e:
            print(f"MQTT Not Connected {e}\n")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker.")
            client.subscribe("/tiot/group6/temperature")
            client.subscribe("/tiot/group6/led")
           
            client.subscribe("smart_home/actuators/+/command")
            print("Subscribed to Arduino and Actuator topics.")
        else:
            print(f"Failed to connect to MQTT broker, return code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            sensor_data = json.loads(payload)
            
            #SenML is expected so we can just append
            self.postEvent(sensor_data)
            print("MQTT Recived")
        except Exception as e:
            print(f"MQTT Error: {e}")

    def GET(self, *path, **query):
        match len(path):
            case 0:  # Handled /log
                if len(query) > 0 and "room" in query and "since" in query:
                    res = list()  
                    for e in self.events:
                        if query["room"] in e.get("bn", "") and e.get("e", [{}])[0].get("t", 0) >= float(query["since"]):
                            res.append(e)
                    return json.dumps(res).encode('utf-8')
                else:
                    return json.dumps(self.events).encode('utf-8')
                    
            case 1: # Handled /log/<room>
                if path[0] in self.roomNames:
                    res = list() 
                    for e in self.events:
                        if path[0] in e.get("bn", ""):
                            res.append(e)
                    return json.dumps(res).encode('utf-8')
        return json.dumps([]).encode('utf-8')

    def postEvent(self, body):
        self.events.append(body)
        return

    def POST(self, *path, **query):
        body= cherrypy.request.body.read().decode('utf-8')
        bodyDict= json.loads(body.strip())
        self.events.append(bodyDict)
        return "Event Logged".encode('utf-8')

    def DELETE(self, *path, **query):
        if "before" in query.keys():
            time_limit=float(query["before"])
            count=0
            newList=list()
            for e in self.events:
                event_time = e.get("t", e.get("bt", 0))
                if event_time < time_limit:
                    count += 1
                else:
                    newList.append(e)
            self.events=newList
            return str(count).encode('utf-8')
        else:
            raise cherrypy.HTTPError(400, "Missing required query parameter: before")
               
if __name__ == '__main__':
    conf = {
        '/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on': True,
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Content-Type', 'application/json')]} 
        }
    
    cherrypy.tree.mount(EventLogv2(), '/log', conf)
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 9090})
    cherrypy.engine.start()
    cherrypy.engine.block()