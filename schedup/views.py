from schedup.base import BaseHandler
from schedup.models import EventInfo


class MainPage(BaseHandler):
    URL = "/"
    
    def get(self):
        self.render_response('index.html', 
            title = "SchedUp", 
            subtitle = "The way to schedule up", 
            content = "hello moishe")

# Tomer + send emails
class LoginPage(BaseHandler):
    URL = "/login"
    
    def get(self):
        self.render_response('index.html')

# Shir
class MyEventsPage(BaseHandler):
    URL = "/myevents"
    
    def get(self):
        EventInfo.get_owner_events()
        self.render_response('index.html')

# Shir
class InvitedToPage(BaseHandler):
    URL = "/invited"
    
    def get(self):
        EventInfo.get_participating_events()
        self.render_response('index.html')

# Ofir
class NewEventPage(BaseHandler):
    URL = "/new"
    
    def post(self):
        evt = EventInfo(title = self.request["title"], start_date = self.request["start_date"])
        evt.token = "random token"
        evt.save()

# Yana
class GuestPage(BaseHandler):
    URL = "/guest/(.*)"
    
    def get(self, token):
        evt = EventInfo.query(token == token).get()
        self.render_response('index.html')
    
    def post(self, token):
        evt = EventInfo.query(token == token).get()
        if self.request["answer"]:
            evt.confirmed.append(token)



'''

MVC - model view container
1. login with google account, ask permissions for calendar, email, (contacts?)
2. finish models 
3. create simple event form
4. my meetings page/my invites page
5. recipient page (yes/no)


Hello <>
Moshe invited you to a meeting.
<Click here http://schedup.appspot.com/guest/983329847376783745>
    
'''
        
      
      
