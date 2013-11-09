from schedup.base import BaseHandler


class MainPage(BaseHandler):
    URL = "/"
    
    def get(self):
        self.render_response('index.html', 
            title = "SchedUp", 
            subtitle = "The way to schedule up", 
            content = "hello moishe")

class FooPage(BaseHandler):
    URL = "/foo"
    
    def get(self):
        self.render_response('index.html', 
            title = "SchedUp", 
            subtitle = "The way to schedule up", 
            content = "hello baruch")

