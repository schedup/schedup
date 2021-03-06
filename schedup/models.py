import time
from google.appengine.ext import ndb
from datetime import timedelta
import datetime
import logging

class UserProfile(ndb.Model):
    email = ndb.StringProperty(required=True)
    fullname = ndb.StringProperty()
    google_id = ndb.StringProperty()
    facebook_id = ndb.StringProperty()
    facebook_token = ndb.StringProperty()
    gcm_id = ndb.StringProperty()   # google cloud messaging client ID
    seen_tutorial1 = ndb.BooleanProperty()
    seen_tutorial2 = ndb.BooleanProperty()

    def get_owner_events(self):
        return EventInfo.query(EventInfo.owner == self.key)
    
    def get_participating_events_fb(self):
        logging.info("CHECK: %r",self.facebook_id)
        return EventInfo.query(EventInfo.guests.email == self.facebook_id)
    
    def get_participating_events(self):
        return EventInfo.query(EventInfo.guests.email == self.email)
        
    
    def count_invited_to(self):
        count = 0
        mintime = datetime.datetime.today() - timedelta(days = 3)
        for evt in EventInfo.query(EventInfo.guests.email == self.email, EventInfo.guests.status == "pending").filter(EventInfo.end_window >= mintime):
            if evt.status != "canceled":
                for guest in evt.guests:
                    if (guest.email == self.email and guest.status == "pending"):
                        logging.info("TITLE: %r", evt.title)    
                        count += 1
        for evt in EventInfo.query(EventInfo.guests.email == self.facebook_id, EventInfo.guests.status == "pending").filter(EventInfo.end_window >= mintime):
            if evt.status != "canceled":
                for guest in evt.guests:
                    if (guest.email == self.facebook_id and guest.status == "pending"):
                        logging.info("TITLE: %r", evt.title)
                        count += 1
        return count

    def sanitized_email(self):
        good = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890-_'
        return "".join((ch if ch in good else "_") for ch in self.email)


class EventGuest(ndb.Model):
    # always expected to be set (if FB then FB id)
    email = ndb.StringProperty()
    # may be set if the guest is a user
    name = ndb.StringProperty()
    user = ndb.KeyProperty(UserProfile)
    token = ndb.StringProperty()
    selected_times= ndb.PickleProperty()
    status = ndb.StringProperty(choices=["accept","decline","pending"], default="pending")
    seenInfo = ndb.StringProperty(choices=["not seen", "about to see", "seen"], default="not seen")
    seen_tutorial1 = ndb.BooleanProperty()
    seen_tutorial2 = ndb.BooleanProperty()

    
    @property
    def fullname(self):
        return self.user.get().fullname if self.user else (self.name if self.name else self.email)
    
    def sanitized_email(self):
        good = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890-_'
        return "".join((ch if ch in good else "_") for ch in self.email)
    
    def has_seen_tutorial1(self):
        if self.seen_tutorial1:
            return True
        if self.user:
            return self.user.seen_tutorial1
        return False

    def has_seen_tutorial2(self):
        if self.seen_tutorial2:
            return True
        if self.user:
            return self.user.seen_tutorial2
        return False


class EventInfo(ndb.Model):
    owner = ndb.KeyProperty(UserProfile, required = True)
    owner_token = ndb.StringProperty(required = True)
    guests = ndb.StructuredProperty(EventGuest, repeated = True)
    created_at = ndb.DateTimeProperty(auto_now_add = True)
    status = ndb.StringProperty(choices=["sent","canceled","pending"], default="pending")
    evtid = ndb.StringProperty()
    owner_selected_times= ndb.PickleProperty()
    new_notifications = ndb.IntegerProperty(default = 0)
    first_owner_save = ndb.BooleanProperty()
    source = ndb.StringProperty(choices=["google", "facebook"], default = "google")
    
    daytime = ndb.StringProperty(repeated = True)
    type = ndb.StringProperty()
    title = ndb.StringProperty(required = True)
    description = ndb.StringProperty()
    start_window = ndb.DateProperty(required = True)
    end_window = ndb.DateProperty(required = True)
    duration = ndb.IntegerProperty(required = True)
    location = ndb.StringProperty()
    start_time = ndb.DateTimeProperty()
    end_time = ndb.DateTimeProperty()
    
    @property
    def owner_fullname(self):
        owner = self.owner.get()
        return owner.fullname or owner.email
    
    @classmethod
    def get_by_guest_token(cls, token):
        evt = EventInfo.query(EventInfo.guests.token == token).get()
        if evt:
            for guest in evt.guests:
                if guest.token == token:
                    return evt, guest
        return None, None
    
    @classmethod
    def get_by_token(cls, user_token):
        evt = cls.get_by_owner_token(user_token)
        if evt:
            return True, evt, evt.owner.get()
        evt, gst = cls.get_by_guest_token(user_token)
        if evt:
            return False, evt, gst
        return None, None, None
    
    def get_token_for(self, user):
        for guest in self.guests:
            if guest.user == user.key:
                return guest.token
        return None
    
    def get_guests_by_status(self, status):
        return [gst for gst in self.guests if gst.status == status]

    @classmethod
    def get_by_owner_token(cls, owner_token):
        return cls.query(cls.owner_token == owner_token).get()
    
    def get_response(self,user):
        for guest in self.guests:
            if guest.user==user.key:
                return guest.status
    
    def past_event(self):
        if (self.end_time-datetime.datetime.now())>datetime.timedelta(days=-2):
            return True
        return False
        
    def suggest_times(self, max_results = 3):
        time_table = {}
        halfhour = timedelta(minutes = 30)
        # add the owner's votes
        if self.owner_selected_times:
            for start_time, end_time in self.owner_selected_times:
                t = start_time
                while t < end_time:
                    if t not in time_table:
                        time_table[t] = 0
                    time_table[t] += 2
                    t += halfhour
        
        # add guest votes (but only if owner votes intersect with them)
        for guest in self.guests:
            if not guest.selected_times:
                continue
            for start_time, end_time in guest.selected_times:
                t = start_time
                while t < end_time:
                    if t not in time_table:
                        time_table[t] = 0
                    time_table[t] += 1
                    t += halfhour
        
        # sort time slots first by num of votes (more is better), then by date (sooner is better)
        sorted_times = sorted(time_table, key = lambda k: (time_table[k], -time.mktime(k.timetuple())), reverse = True)
        
        # merge time slots into ranges (up to max_results)
        ranges = []
        for slot in sorted_times:
            if len(ranges) >= max_results:
                break
            elif not ranges:
                ranges.append((slot, slot + halfhour))
                continue
            s, e = ranges[-1]
            if e == slot:
                ranges[-1] = (s, slot + halfhour)
            elif s == slot + halfhour:
                ranges[-1] = (slot, e)
            else:
                ranges.append((slot, slot + halfhour))
        return ranges










