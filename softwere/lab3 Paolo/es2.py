import cherrypy
import time
import random
import json

class SmartHomeSensorService:
    exposed = True
    rooms = {"living_room", "kitchen", "bedroom"}
    sensors = {"temperature", "humidity", "motion"}
    
    def GET(self, *path, **query):
        
        if not path or path[0] != 'sensors':
            raise cherrypy.HTTPError(404, "Endpoint not found. Use /sensors")

        sub_path = path[1:]

        if len(sub_path) == 0:
            full_response = []
            for r in self.rooms:
                for s in self.sensors:
                    full_response.extend(self._generate_senml(r, s))
            return json.dumps(full_response).encode('utf-8')

        elif len(sub_path) == 1:
            room = sub_path[0]
            if room not in self.rooms:
                raise cherrypy.HTTPError(404, json.dumps({
                    "error": "room not found",
                    "available_rooms": list(self.rooms)
                }))
            
            room_response = []
            for s in self.sensors:
                room_response.extend(self._generate_senml(room, s))
            return json.dumps(room_response).encode('utf-8')

        elif len(sub_path) >= 2:
            room = sub_path[0]
            device = sub_path[1]

            if room not in self.rooms:
                raise cherrypy.HTTPError(404, json.dumps({"error": "room not found"}))
            
            if device not in self.sensors:
                raise cherrypy.HTTPError(400, json.dumps({"error": "unknown sensor type"}))
            
            single_response = self._generate_senml(room, device)
            return json.dumps(single_response).encode('utf-8')

    def _generate_senml(self, room, sensor_type):
        
        base_name = f"iot/smarthome/{room}/"
        
        if sensor_type == "temperature":
            value = round(random.uniform(15, 28), 2)
            unit = "°C" 
        elif sensor_type == "humidity":
            value = round(random.uniform(30, 80), 2)
            unit = "%RH" 
        elif sensor_type == "motion":
            value = random.choice([True, False])
            unit = None
        
        return [{
            "bn": base_name,
            "bt": time.time(),
            "n": sensor_type,
            "u": unit,
            "v": value
        }]

if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')]
        }
    }
    cherrypy.config.update({'server.socket_port': 9090})
    cherrypy.tree.mount(SmartHomeSensorService(), '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()