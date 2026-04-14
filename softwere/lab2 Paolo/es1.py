import cherrypy
import random
from datetime import datetime, time, timezone
import json
import math



class SensorStatusChecker:
    def __init__(self):
        self.known_sensors = {
            'temperature','pressure','humidity','motion'}
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def check(self, sensorname = None):
        if sensorname is None:
            raise cherrypy.HTTPError(400, 'Missing sensorname parameter')
        
        status = random.choice(['online', 'offline'])

        timestamp = datetime.now(timezone.utc).isoformat()

        return {
            'sensorname': sensorname,
            'status': status,
            'timestamp': timestamp
        }
        
class ThresholdAlertSystem:
    def __init__(self):
        self.thresholds = {}      
        self.alerts = []

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def set_threshold(self):
        if cherrypy.request.method != 'GET':
            return self.thresholds
        if cherrypy.request.method != 'POST':
            input_data = cherrypy.request.json
            sensor = input_data.get('sensor')
            min = input_data.get('min')
            max = input_data.get('max')

            if min > max:
                raise cherrypy.HTTPError(400, 'Min threshold cannot be greater than max threshold')
            self.thresholds[sensor] = {'min': min, 'max': max}
            return{"status":"success", "message": f'Thresholds for {sensor} set to min: {min}, max: {max}'}
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def check_threshold(self):
        if cherrypy.request.method != 'POST':
            input_data = cherrypy.request.json
            sensor = input_data.get('sensor')
            value = input_data.get('value')
            if sensor not in self.thresholds:
                raise cherrypy.HTTPError(404, 'Thresholds for this sensor not set')
            thresholds = self.thresholds[sensor]
            alert_triggered = False
            direction = None
            if (value < thresholds['min']):
                alert_triggered = True
                direction = 'LOW'
            elif (value > thresholds['max']):
                alert_triggered = True
                direction = 'HIGH'

            response = {"alert":alert_triggered}    
            if alert_triggered:
                alert_entry = {
                    'sensor': sensor,
                    'value': value,
                    'direction': direction,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                self.alerts.append(alert_entry)
                response["details"] = alert_entry
            
            return response
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_alerts(self,sensor = None):
        if sensor is None:
            return self.alerts
        
        filtered = [a for a in self.alerts if a['sensor'] == sensor]
        return filtered

class RoomService:
    def __init__(self):
        self.rooms = {}
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def rooms(self, *uri, **params):
        method = cherrypy.request.method
        uri_len = len(uri)

        if charrypy.request.method == 'GET' and uri_len == 0:
            return list(self.rooms.keys())

        if (uri_len >= 1):
            room_name = uri[0]
            if method == 'POST':
                if room_name not in self.rooms:
                    self.rooms[room_name] = {}
            device_data = cherrypy.request.json
            device_id = f'd{len(self.rooms[room_name]) + 1:03d}'
            self.rooms[room_name][device_id] = device_data
            return{
                "message": f'Device added',
                "device_id": device_id,
                "room": room_name
            }
        
        if room_name not in self.rooms:
            raise cherrypy.HTTPError(404, 'Room not found')

        if method == 'GET' and uri_len == 1:
            return self.rooms[room_name]

        if uri_len == 2:
            device_id = uri[1]

            if method =='GET':
                if device_id not in self.rooms[room_name]:
                    raise cherrypy.HTTPError(404, 'Device not found')
                return self.rooms[room_name][device_id]
            if metghod == 'DELETE':
                if device_id not in self.rooms[room_name]:
                    raise cherrypy.HTTPError(404, 'Device not found')
                deleted_device = self.rooms[room_name].pop(device_id)
                return {"message": "Device removed", "device": deleted_device}

        raise cherrypy.HTTPError(400, 'Invalid request')


class SensorSignalSimulator:
    SENSOR_RANGES = {
            'temperature': (-20, 50, '°C'),
            'pressure': (950, 1050, 'hPa'),
            'humidity': (0, 100, '%'),
            'co2': (400, 5000, 'ppm'),
            'light': (0, 1000, 'lux')
        }

    def getvalue(self, sensor, i, n, model):
        low, high, unit = self.SENSOR_RANGES[sensor]
        mid = (low + high) / 2
        amp = (high - low) / 2
        if model == 'random':
            return random.uniform(low, high)
        elif model == "sine":
            return mid + amp * math.sin(2 * math.pi * i / n)
        elif model == "step":
            return low if i < n / 2 else high
        elif model == "sawtooth":
            return low + (high - low) * (i / n)
        else:
            raise ValueError('Invalid model type')
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def stream(self,name = None,samples = 10, interval = 0):
        if name is None or name not in self.SENSOR_RANGES:
            raise cherrypy.HTTPError(400, 'Invalid or missing sensor name')
        min_val, max_val, unit = self.SENSOR_RANGES[name]
        data_stream = []
        for val in range(samples):
            value = random.uniform(min_val, max_val)
            data_stream.append({'t':val,'value': round(value, 2), 'unit': unit})
            if interval > 0:
                time.sleep(interval)

        return {"sensor": name, "model": "random", "samples": data_stream}
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def simulate(self,name = None, samples = 10, model = 'random'):
        if name is None or name not in self.SENSOR_RANGES:
            raise cherrypy.HTTPError(400, 'Invalid or missing sensor name')
        n = int(samples)
        unit = self.SENSOR_RANGES[name][2]
        data_stream = []
        for val in range(samples):
            value = self.getvalue(name, val, n, model)
            data_stream.append({'t':val,'value': round(value, 2), 'unit': unit})

        return {"sensor": name, "model": model, "samples": data_stream}

class CommandDispatcher:
    ACTUATORS_TYPES = {
            'LED': ['on', 'off', 'toggle'],
            'fan': ['on', 'off', 'set'],
            'lock': ['lock', 'unlock'],
            'heater': ['on', 'off', 'set_temperature']
        }
    def __init__(self):
        self.actuators = {
            'led_1': {'type': 'LED', 'state': 'off', 'last_cmd': None},
            'fan_1': {'type': 'fan', 'state': 'off', 'last_cmd': None},
            'lock_1': {'type': 'lock', 'state': 'locked', 'last_cmd': None},
        }
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def command(self,aid = None):
        method = cherrypy.request.method
        if method == 'GET' and aid is None:
            return self.actuators
        if aid not in self.actuators:
            raise cherrypy.HTTPError(404, 'Actuator not found')
        if method == 'GET':
            return self.actuators[aid]
        if method == 'POST':
            input_data = cherrypy.request.json
            action = data.get('action')
            value = data.get('value')
            type = self.actuators[aid]['type']

            if action not in self.ACTUATORS_TYPES[type]:
                raise cherrypy.HTTPError(400, 'Invalid action for this actuator type')
            
            new_state = self.actuators[aid]['state']

            if action == 'toggle':
                new_state = 'on' if self.actuators[aid]['state'] == 'off' else 'off'
            elif action in ['on', 'off', 'lock', 'unlock']:
                new_state = action
            elif action in ['set', 'set_temperature']:
                new_state = value if value else "unknown"
            
            timestamp = datetime.now(timezone.utc).isoformat()
            cmd_record = [{'action': action, 'value': value, 'timestamp': timestamp}]

            self.actuators[aid]['state'] = new_state
            self.actuators[aid]['last_cmd'] = cmd_record
            return {
                "message": f'Command {action}executed on {aid}',
                "new_state": new_state,
            }







if __name__ == '__main__':
    conf = {
        '/': {
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on': True,
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Content-Type',
        'application/json')]
            }
        }
    cherrypy.tree.mount(MyService(), '/', conf)
    cherrypy.config.update({'server.socket_port': 9090})
    cherrypy.engine.start()
    cherrypy.engine.block()
    cherrypy.quickstart(SensorStatusChecker())
    cherrypy.quickstart(ThresholdAlertSystem())
    cherrypy.quickstart(RoomService())




