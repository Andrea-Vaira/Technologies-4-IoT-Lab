from part1_sw import *
from part2_sw import *
import cherrypy

if __name__ == '__main__':
    conf = {
        '/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on': True,
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Content-Type', 'application/json')]} 
        }
    
    cherrypy.tree.mount(SmartHomeService (), '/', conf)
    cherrypy.tree.mount(EventLog (), '/log', conf)
    cherrypy.tree.mount(Catalog (), '/', conf)
    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    cherrypy.config.update({'server.socket_port': 9090})
    cherrypy.engine.start()
    cherrypy.engine.block()