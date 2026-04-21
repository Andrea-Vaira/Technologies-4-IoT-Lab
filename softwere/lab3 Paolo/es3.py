import cherrypy
import time
import json

class SmartHomeService:
    exposed = True

    def __init__(self):
        self.rooms = {"living_room", "kitchen", "bedroom"}
        self.device_types = {"thermostat", "lights", "blinds"}
        
        self.actuators = {
            room: {
                "thermostat": 20.0, 
                "lights": False,     
                "blinds": 0          
            } for room in self.rooms
        }

    def GET(self, *path, **query):
        if not path or path[0] != 'sensors':
            raise cherrypy.HTTPError(404, "Base path must be /sensors")

        sub_path = path[1:]

        if len(sub_path) == 0:
            full_response = []
            for r in sorted(self.rooms):
                for d in sorted(self.device_types):
                    full_response.extend(self._generate_senml(r, d))
            return json.dumps(full_response).encode('utf-8')

        room = sub_path[0]
        if room not in self.rooms:
            raise cherrypy.HTTPError(404, f"Room '{room}' not found")

        if len(sub_path) == 1:
            room_response = []
            for d in sorted(self.device_types):
                room_response.extend(self._generate_senml(room, d))
            return json.dumps(room_response).encode('utf-8')

        device = sub_path[1]
        if device not in self.device_types:
            raise cherrypy.HTTPError(400, f"Unknown device type: {device}")
        
        return json.dumps(self._generate_senml(room, device)).encode('utf-8')

    def PUT(self, *path, **query):

        if len(path) < 3 or path[0] != 'sensors':
            raise cherrypy.HTTPError(404, "Endpoint must follow /sensors/<room>/<device>")

        room, device = path[1], path[2]

        content_length = int(cherrypy.request.headers.get('Content-Length', 0))
        raw_body = cherrypy.request.body.read(content_length)

        try:
            data = json.loads(raw_body)
            record = data[0] if isinstance(data, list) else data
            if 'v' not in record: 
                raise ValueError
            new_value = record['v']
        except (ValueError, json.JSONDecodeError, IndexError):
            raise cherrypy.HTTPError(422, "Malformed SenML body. 'v' field required.")

        if room not in self.rooms or device not in self.device_types:
            raise cherrypy.HTTPError(404, "Room or Device not found")

        if device == "thermostat":
            if not isinstance(new_value, (int, float)):
                raise cherrypy.HTTPError(400, "Thermostat value must be numeric")
            if not (10 <= new_value <= 30):
                raise cherrypy.HTTPError(400, "Out of range: Thermostat must be 10-30°C")
        
        elif device == "blinds":
            if not (0 <= new_value <= 100):
                raise cherrypy.HTTPError(400, "Out of range: Blinds must be 0-100%")
        
        elif device == "lights":
            if not isinstance(new_value, bool):
                raise cherrypy.HTTPError(400, "Lights must be true or false")

        self.actuators[room][device] = new_value
        
        return json.dumps(self._generate_senml(room, device)).encode('utf-8')

    def _generate_senml(self, room, device):
        """Helper to format data into SenML JSON."""
        units = {"thermostat": "C°", "blinds": "%", "lights": None}
        return [{
            "bn": f"home/{room}/", 
            "n": device,
            "u": units.get(device),
            "v": self.actuators[room][device],
            "t": time.time()
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
    cherrypy.tree.mount(SmartHomeService(), '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()