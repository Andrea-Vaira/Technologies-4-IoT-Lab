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
        since = query.get("since",0)
        if(len(path) > 0):
            if(room != "" and room != path[0]):
                raise cherrypy.HTTPError(403,"Arguments passed through path and query in conflict")
            else:
                room = path[0]
        res = []
        for log in self.logs.values():
            for event in log['e']:
                if room in event['n'] and log['bt'] > since:
                    res.append(event)
        return json.dumps(res).encode('utf-8')
    
    def DELETE(self,*path,**query):
        epoch = query.get("since",None)
        if(epoch == None):
            raise cherrypy.HTTPError(403,"Epoch in query is mandatory")
        pre = len(self.logs)
        self.logs[:] = [x for x in self.logs if x['bt'] >= epoch]
        post = len(self.logs)
        return pre - post
    
                    



