import cherrypy
from SmartHomeService import *
from SmartHome import *
from EventLog import *
from Catalog import *
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
 eventLog = EventLog()
 catalog = CatalogClient()
 myHome = SmartHome(eventLog,catalog)
 sensorService = SmartHomeSensorService(myHome)
 actuatorService = SmartHomeActuatorService(myHome)
 cherrypy.tree.mount(sensorService, '/sensor', conf)
 cherrypy.tree.mount(actuatorService, '/actuator', conf)
 cherrypy.tree.mount(catalog.catalog,'/catalog',conf)
 cherrypy.tree.mount(eventLog,'/log',conf)
 cherrypy.config.update({'server.socket_port': 8080})
 cherrypy.config.update({'server.socket_host': '127.0.0.1'})
 cherrypy.engine.start()
 cherrypy.engine.block()