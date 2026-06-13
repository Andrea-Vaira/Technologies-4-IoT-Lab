#Class of Software Laboratory Part 1
import cherrypy
import json

class EventLog(object):
    exposed = True

    def __init__(self):
        self.logs = dict()
        self.logID = 0
    
    def add(self,sml):
        baseName = sml['bn']
        newEvents = []
        
        for event in sml['e']:
            newEvent = event.copy()
            newEvent['n'] = baseName + event['n']
            newEvents.append(newEvent)

        finalSml = {
                'bt' : sml['bt'],
                'e' : newEvents
            }
        
        self.logs[self.logID] = finalSml
        self.logID += 1
            
        return finalSml
    
    def POST(self,*path,**query):
        try:
            sml = json.loads(cherrypy.request.body.read())
            self.add(sml)
            return sml
        except ValueError:
            raise cherrypy.HTTPError(422,"Unprocessable entity: SenML body is malformed")
        
    def GET(self,*path,**query):
        room = query.get("room","")
        since = int(query.get("since",0))
        type = query.get("type","")

        if(len(path) > 0):
            if(room != "" and room != path[0]):
                raise cherrypy.HTTPError(403,"Arguments passed through path and query in conflict")
            else:
                room = path[0]
                
        res = []
        for log in self.logs.values():
            for event in log['e']:
                if room in event['n'] and log['bt'] > since and type in event["n"]:
                    res.append(event)
        return json.dumps(res).encode('utf-8')
    
    def DELETE(self,*path,**query):
        epoch = int(query.get("before",-1))
        if(epoch == -1):
            raise cherrypy.HTTPError(403,"Epoch in query is mandatory")
        pre = len(self.logs)
        self.logs = {id_log: log for id_log, log in self.logs.items() if log.get('bt', 0) >= epoch}
        post = len(self.logs)
        return str(pre - post).encode()
    
                    



