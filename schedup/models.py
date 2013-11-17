from google.appengine.ext import ndb
from datetime import datetime, timedelta


class UserProfile(ndb.Model):
    email = ndb.StringProperty(required=True)
    fullname = ndb.StringProperty()
    google_id = ndb.StringProperty()
    facebook_id = ndb.StringProperty()

    def get_owner_events(self):
        return EventInfo.query(EventInfo.owner == self.key)
    
    def get_participating_events(self):
        return EventInfo.query(EventInfo.recepient_emails == self.email)


class EventInfo(ndb.Model):
    owner = ndb.KeyProperty(UserProfile, required = True)
    recepients = ndb.KeyProperty(UserProfile, repeated = True)
    confirmed = ndb.KeyProperty(UserProfile, repeated = True)
    tokens = ndb.StringProperty(repeated = True)
    daytime = ndb.StringProperty(repeated = True)
    type = ndb.StringProperty()
    title = ndb.StringProperty(required = True)    
    description = ndb.StringProperty()
    start_window = ndb.DateProperty(required = True)
    end_window = ndb.DateProperty(required = True)
    start_time = ndb.DateTimeProperty()
    end_time = ndb.DateTimeProperty()








