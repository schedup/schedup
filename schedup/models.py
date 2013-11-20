from google.appengine.ext import ndb


class UserProfile(ndb.Model):
    email = ndb.StringProperty(required=True)
    fullname = ndb.StringProperty()
    google_id = ndb.StringProperty()
    facebook_id = ndb.StringProperty()

    def get_owner_events(self):
        return EventInfo.query(EventInfo.owner == self.key)
    
    def get_participating_events(self):
        return EventInfo.query(EventInfo.guests.user == self.key)


class EventGuest(ndb.Model):
    # extactly one of these must be set {{
    user = ndb.KeyProperty(UserProfile)
    email = ndb.StringProperty()
    # }}
    token = ndb.StringProperty()
    status = ndb.StringProperty()


class EventInfo(ndb.Model):
    owner = ndb.KeyProperty(UserProfile, required = True)
    owner_token = ndb.StringProperty(required = True)
    guests = ndb.StructuredProperty(EventGuest, repeated = True)
    
    daytime = ndb.StringProperty(repeated = True)
    type = ndb.StringProperty()
    title = ndb.StringProperty(required = True)
    description = ndb.StringProperty()
    start_window = ndb.DateProperty(required = True)
    end_window = ndb.DateProperty(required = True)
    
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







