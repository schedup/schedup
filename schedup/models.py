from google.appengine.ext import ndb
from datetime import timedelta


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

    title = ndb.StringProperty()    
    start_time = ndb.DateTimeProperty(required = True)
    duration_minutes = ndb.IntegerProperty(required = True)

    @property
    def end_time(self):
        return self.start_time + timedelta(minutes = self.duration_minutes)
















