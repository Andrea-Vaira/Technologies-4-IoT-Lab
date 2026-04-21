import cherrypy
import time
import json

class EventLogger:
    def __init__(self):
        self.logs = []
        self.index = 0

    def add_event(self, smlData):
        if not isinstance(smlData, list):
            smlData = [smlData]
        for record in smlData:
            # CORREZIONE: record.copy() è un metodo, servono le parentesi
            event = record.copy() 
            event['id'] = self.index + 1
            # Se il record non ha già un tempo, lo aggiungiamo
            if 'bt' not in event and 't' not in event:
                event['t'] = time.time()
            self.logs.append(event)
            self.index += 1

    def get_logs(self, room=None, since=None, before=None):
        filtered = self.logs
        if room:
            filtered = [log for log in filtered if room in log.get('bn', '')]
        if since is not None:
            filtered = [log for log in filtered if log.get('t', log.get('bt', 0)) >= float(since)]
        if before is not None:
            filtered = [log for log in filtered if log.get('t', log.get('bt', 0)) < float(before)]
        return filtered

    def delete_logs(self, before):
        original_count = len(self.logs)
        self.logs = [log for log in self.logs if log.get('t', log.get('bt', 0)) >= float(before)]
        return original_count - len(self.logs)

class SmartHomeService:
    exposed = True

    def __init__(self):
        self.rooms = {"living_room", "kitchen", "bedroom"}
        self.device_types = {"thermostat", "lights", "blinds"}
        self.actuators = {
            room: {"thermostat": 20.0, "lights": False, "blinds": 0} 
            for room in self.rooms
        }
        self.event_logger = EventLogger()

    def GET(self, *path, **query):
        if path and path[0] == 'log':
            room = path[1] if len(path) > 1 else query.get('room')
            results = self.event_logger.get_logs(
                room=room, 
                since=query.get('since'), 
                before=query.get('before')
            )
            return json.dumps(results).encode('utf-8')
        
        if not path or path[0] != 'sensors':
            raise cherrypy.HTTPError(404, "Base path must be /sensors o /log")

        sub_path = path[1:]
        if len(sub_path) == 0:
            res = []
            for r in sorted(self.rooms):
                for d in sorted(self.device_types):
                    res.extend(self._generate_senml(r, d))
            return json.dumps(res).encode('utf-8')

        room = sub_path[0]
        if room not in self.rooms:
            raise cherrypy.HTTPError(404, f"Room '{room}' not found")

        if len(sub_path) == 1:
            res = []
            for d in sorted(self.device_types):
                res.extend(self._generate_senml(room, d))
            return json.dumps(res).encode('utf-8')

        device = sub_path[1]
        if device not in self.device_types:
            raise cherrypy.HTTPError(400, f"Unknown device type: {device}")
        
        smlData = self._generate_senml(room, device)
        # Integrazione: Logghiamo la lettura
        self.event_logger.add_event(smlData)
        return json.dumps(smlData).encode('utf-8')

    def POST(self, *path, **query):
        if not path or path[0] != 'log':
            raise cherrypy.HTTPError(404)
        cl = int(cherrypy.request.headers.get('Content-Length', 0))
        raw_body = cherrypy.request.body.read(cl)
        try:
            data = json.loads(raw_body)
            self.event_logger.add_event(data)
            return "Event logged".encode('utf-8')
        except:
            raise cherrypy.HTTPError(422, "Malformed SenML")

    def PUT(self, *path, **query):
        if len(path) < 3 or path[0] != 'sensors':
            raise cherrypy.HTTPError(404, "Use /sensors/<room>/<device>")

        room, device = path[1], path[2]
        cl = int(cherrypy.request.headers.get('Content-Length', 0))
        raw_body = cherrypy.request.body.read(cl)

        try:
            data = json.loads(raw_body)
            record = data[0] if isinstance(data, list) else data
            new_value = record['v']
        except:
            raise cherrypy.HTTPError(422, "Malformed SenML")

        # Validazione range (come da Esercizio 03)
        if device == "thermostat" and not (10 <= new_value <= 30):
            raise cherrypy.HTTPError(400, "Thermostat 10-30°C only")

        self.actuators[room][device] = new_value
        smlData = self._generate_senml(room, device)
        
        # Integrazione: Logghiamo il comando dell'attuatore
        self.event_logger.add_event(smlData)
        return json.dumps(smlData).encode('utf-8')

    def DELETE(self, *path, **query):
        if not path or path[0] != 'log' or 'before' not in query:
            raise cherrypy.HTTPError(400, "Missing 'before' parameter")
        count = self.event_logger.delete_logs(query['before'])
        return json.dumps({"deleted": count}).encode('utf-8')

    def _generate_senml(self, room, device):
        units = {"thermostat": "C°", "blinds": "%", "lights": None}
        return [{
            "bn": f"home/{room}/", 
            "n": device,
            "u": units.get(device),
            "v": self.actuators[room][device],
            "t": time.time()
        }]

if __name__ == '__main__':
    conf = {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                  'tools.response_headers.on': True,
                  'tools.response_headers.headers': [('Content-Type', 'application/json')]}}
    cherrypy.tree.mount(SmartHomeService(), '/', conf)
    cherrypy.config.update({'server.socket_port': 9090})
    cherrypy.engine.start()
    cherrypy.engine.block()