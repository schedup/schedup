from google.appengine.ext import ndb
from google.appengine.api.validation import Repeated


class UserProfile(ndb.Model):
    email = ndb.StringProperty(required=True)
    fullname = ndb.StringProperty()
    google_id = ndb.StringProperty()
    facebook_id = ndb.StringProperty()

    def get_owner_events(self):
        return EventInfo.query(EventInfo.owner == self.key)
    
    def get_participating_events(self):
        return EventInfo.query(EventInfo.guests.user == self.key)
    
    def count_invited_to(self):
        count = 0
        for evt in EventInfo.query(EventInfo.guests.user == self.key, EventInfo.guests.status == "pending"):
            for guest in evt.guests:
                if guest.user == self.key and guest.status == "pending":
                    count += 1
        return count

               
class EventGuest(ndb.Model):
    # extactly one of these must be set {{
    user = ndb.KeyProperty(UserProfile)
    email = ndb.StringProperty()
    # }}
    token = ndb.StringProperty()
    selected_times= ndb.PickleProperty()
    status = ndb.StringProperty(choices=["accept","decline","pending"], default="pending")


class EventInfo(ndb.Model):
    owner = ndb.KeyProperty(UserProfile, required = True)
    owner_token = ndb.StringProperty(required = True)
    guests = ndb.StructuredProperty(EventGuest, repeated = True)
    created_at = ndb.DateTimeProperty(auto_now_add = True)
    status = ndb.StringProperty(choices=["sent","canceled","pending"], default="pending")
    evtid = ndb.StringProperty()
    
    daytime = ndb.StringProperty(repeated = True)
    type = ndb.StringProperty()
    title = ndb.StringProperty(required = True)
    description = ndb.StringProperty()
    start_window = ndb.DateProperty(required = True)
    end_window = ndb.DateProperty(required = True)
    duration = ndb.IntegerProperty(required = True)
    start_time = ndb.DateTimeProperty()
    end_time = ndb.DateTimeProperty()
    
    @classmethod
    def get_by_guest_token(cls, token):
        evt = EventInfo.query(EventInfo.guests.token == token).get()
        if evt:
            for guest in evt.guests:
                if guest.token == token:
                    return evt, guest
        return None, None
    
    def get_token_for(self, user):
        for guest in self.guests:
            if guest.user == user.key:
                return guest.token
        return None
    
    def get_guests_by_status(self, status):
        return [gst for gst in self.guests if gst.status == status]


    def has_responded(self,user):
        for guest in self.guests:
            if guest.user==user.key:
                return guest.status!="pending"





