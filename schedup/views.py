from schedup.base import BaseHandler, oauth, logged_in
from datetime import datetime, timedelta
from schedup.connector import GoogleConnector
from schedup.models import UserProfile, EventInfo


class MainPage(BaseHandler):
    URL = "/"
    
    def get(self):
        self.render_response('index.html', 
            title = "SchedUp", 
            subtitle = "The way to schedule up", 
            content = "hello moishe")

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

class ContactPage(BaseHandler):
    URL = "/contact"
    
    @oauth.oauth_required
    def get(self):
        from gdata.contacts.client import ContactsClient, ContactsQuery
        from gdata.gauth import ClientLoginToken
        
        client = ContactsClient(source = "SchedUp", auth_token = ClientLoginToken(oauth.credentials.access_token))
        query = ContactsQuery(max_results = 10)
        result = client.GetContacts(q=query)
        self.render_response('index.html', content = repr(result))


class ProfilePage(BaseHandler):
    URL = "/profile"
    
    @logged_in
    def get(self):
        self.render_response('index.html', content = repr(self.user.email))



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
'''

# Yana
class GuestPage(BaseHandler):
    URL = "/guest/(.*)"
    
    def get(self, token):
        #evt = EventInfo.query(token == token).get()
        #self.render_response('index.html')
        

        evt = EventInfo(owner = "Yana", title = "partyyyyyyyy", start_time = datetime(2013, 11, 18, 18, 00), duration_minutes = 800)
        self.render_response("guest.html", content = token, event = evt)
    
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

      
      
