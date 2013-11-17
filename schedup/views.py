import string
import random
import logging
from schedup.base import BaseHandler, oauth
from schedup.base import BaseHandler, oauth, logged_in
from datetime import datetime, timedelta
from schedup.connector import GoogleConnector
from schedup.models import UserProfile, EventInfo

#Dummy events i've created to test events list pages (Shir)
u1 = UserProfile(email="email")
e1 = EventInfo(title="Shir's Birthday", start_time=datetime.strptime("3/4/13 21:00", "%d/%m/%y %H:%M"))
e2 = EventInfo(title="Business Meeting", start_time=datetime.strptime("21/11/13 13:30", "%d/%m/%y %H:%M"))
e3 = EventInfo(title="Night Out!", start_time=datetime.strptime("15/11/13 22:00", "%d/%m/%y %H:%M"))
my_events = [e1, e2, e3]


class MainPage(BaseHandler):
    URL = "/"
    
    def get(self):
        flash =self.session.pop("msg", "")
        self.render_response('index.html',
            title="SchedUp",
            flash=flash,
            subtitle="The way to schedule up",
            content="hello moishe")

class CalPage(BaseHandler):
    URL = "/calendar"
    
    @oauth.oauth_required
    def get(self):
        from apiclient import discovery
        service = discovery.build('calendar', 'v3')
        today = datetime.now()
        events = service.events().list(calendarId='primary', timeMin = today, 
            timeMax = today + timedelta(days = 7)).execute(http=oauth.http())
        self.render_response('index.html', content = repr(events))

        calendar_service = discovery.build('calendar', 'v3')
        result = calendar_service.calendarList().list().execute(http=oauth.http())
        self.render_response('index.html', content=repr(result))

class NewEventPage(BaseHandler):
    URL = "/new"
    
    def post(self):
        date_start_window=datetime.strptime(self.request.get("start"), "%d/%m/%y").date()
        date_end_window=datetime.strptime(self.request.get("end"), "%d/%m/%y").date()      
        
        user = UserProfile.query(UserProfile.email == "kaka").get()
        if not user:
            user = UserProfile(email="kaka")
            user.put()
        tok = id_generator()
        evt = EventInfo(owner=user.key,title=self.request.get("title"),description=self.request.get("description"),
                        start_window=date_start_window, end_window=date_end_window, tokens=[tok] )
        evt.put()
        
        
        # todo:
        # how to connect between the submit button + how does the save work 
        # use jQuery to save to database
        # use DOM interface to add recipients list
        # validate input - mails , valid time window
        # not allowing too long inputs
        logging.info("token=%s", tok)        
        self.session["msg"] = "hello" + evt.title
        self.redirect("/")

class ProfilePage(BaseHandler):
    URL = "/profile"
    
    @logged_in       
    def get(self):
        self.render_response('index.html', content = repr(self.user.email))
            self.render_response('newevent.html')


def id_generator(size=20, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
       

# Shir
class MyEventsPage(BaseHandler):
    URL = "/myevents"
    
    def get(self):
        self.render_response('myevents.html', events = my_events,active="events")

# Shir
class InvitedToPage(BaseHandler):
    URL = "/invited"
    
    def get(self):
        self.render_response('invitedto.html', events = my_events, active="events")


class FooPage(BaseHandler):
    URL = "/foo"
    
    def get(self):
        user1 = UserProfile(email = "yanooosh@gmail.com")
        user1.put()

        evt = EventInfo(owner = user1.key, title = "partyyyyyyyy", start_time = datetime(2013, 11, 18, 18, 00), duration_minutes = 800)
        evt.tokens = ["babayaga"]
        evt.put()


# Yana
class GuestPage(BaseHandler):
    URL = "/guest/(.*)"
    
    def get(self, token):
        evt = EventInfo.query(EventInfo.tokens == token).get()
        if not evt:
            # show some error page to the user
            self.render_response("index.html", content="error")
        else:
            self.render_response("guest.html", event = evt)
    
    def post(self, token):
        evt = EventInfo.query(token == token).get()
        if self.request["answer"]:
            evt.confirmed.append(token)



