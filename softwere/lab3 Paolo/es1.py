import cherrypy
import time
import random
import json


class SmartHomeSensorService:
    exposed = True
    rooms = {"living_room", "kitchen", "bedroom"}
    sensors = {"temperature", "humidity", "motion"}
    
    def GET(self, *path, **query):
        
        room = query.get('room')
        device = query.get('device')

        if room not in self.rooms:
            raise cherrypy.HTTPError(404, json.dumps({
                'error': 'room not found', 
                'available_rooms': list(self.rooms)
            }).encode('utf-8'))
        
        if device not in self.sensors:
            raise cherrypy.HTTPError(400, json.dumps({
                'error': 'unknown sensor type', 
                'valid_types': list(self.sensors)
            }).encode('utf-8'))
        
        senml_response = self._generate_senml(room, device)
        
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps(senml_response).encode('utf-8')
    
    def _generate_senml(self, room, sensor_type):
        """Generate SenML formatted sensor reading"""
        base_name = f"iot/smarthome"
        base_time = time.time()
        
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
            "bt": base_time,
            "n": sensor_type,
            "u": unit,
            "v": value
        }]


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')]
        }
    }
    cherrypy.config.update({'server.socket_port':9090})
    cherrypy.tree.mount(SmartHomeSensorService(), '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()