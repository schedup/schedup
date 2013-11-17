from schedup.base import BaseHandler, oauth
from schedup.models import EventInfo,UserProfile
import string
import random
import logging
from datetime import datetime


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
        calendar_service = discovery.build('calendar', 'v3')
        result = calendar_service.calendarList().list().execute(http=oauth.http())
        self.render_response('index.html', content=repr(result))
'''
class ContactPage(BaseHandler):
    URL = "/contact"
    
    @oauth.oauth_required
    def get(self):
        from gdata.contacts.client import ContactsClient, ContactsQuery
        client = ContactsClient(source="SchedUp", auth_token=oauth.credentials.access_token)
        query = ContactsQuery(max_results=10)
        result = client.GetContacts(q=query)
        self.render_response('index.html', content=repr(result))
'''
        

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
        
    def get(self):
            self.render_response('newevent.html')
            
            
def id_generator(size=20, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
       


'''
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

      
      
