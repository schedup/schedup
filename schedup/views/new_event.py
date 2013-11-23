"""
Create new event flow
"""
import string
import random
from dateutil.parser import parse as parse_datetime
from datetime import timedelta
from schedup.base import BaseHandler, logged_in
from schedup.models import UserProfile, EventInfo, EventGuest
from datetime import datetime
from xmlrpclib import DateTime
from schedup.utils import send_email
from google.appengine.ext import ndb
import logging


class NewEventPage(BaseHandler):
    URL = "/new"
    TOKEN_SIZE = 20
    
    @classmethod
    def generate_token(cls, chars=string.ascii_letters + string.digits):
        return ''.join(random.choice(chars) for _ in range(cls.TOKEN_SIZE))

    @logged_in
    def get(self):
        return self.render_response("new_event.html", post_url=self.URL)

    @logged_in
    def post(self):
        daytime = self.request.params.getall("when")
        guests = []
        for email in self.request.params["guests"].split(";"):
            user = UserProfile.query(UserProfile.email == email).get()
            if user:
                gst = EventGuest(user = user.key, email = email, token = self.generate_token())
            else:
                gst = EventGuest(email=email, token=self.generate_token())
            guests.append(gst)
        
        title = self.request.params["title"]
        fromtime = parse_datetime(self.request.params["fromdate"])
        totime = parse_datetime(self.request.params["todate"])
        
        owner_token = self.generate_token()
        evt = EventInfo(owner = self.user.key, 
            owner_token = owner_token,
            title = title,
            daytime = daytime,
            type = self.request.params.get("type"),
            start_window = fromtime,
            end_window = totime,
            guests = guests,
            description=self.request.params["description"],
        )
        # hack for the first milestone {{
        evt.start_time = evt.start_window.replace(hour = 0, minute = 0, second = 0)
        if "morning" in daytime:
            evt.start_time += timedelta(hours = 8)
        elif "noon" in daytime:
            evt.start_time += timedelta(hours = 12)
        else:
            evt.start_time += timedelta(hours = 20)
        evt.end_time = evt.start_time + timedelta(hours = 2)
        # }}
        evt.put()
        # clear the cache so /my will show this event
        ndb.get_context().clear_cache()
        
        for guest in guests:
            send_email("%s invited you to %s" % (self.user.fullname, title),
                recipient = guest.email,
                html_body = self.render_template("emails/guest.html", 
                        fullname = self.user.fullname, title = title, token = guest.token),
            )
        
        logging.info("Guests: %r", guests)
        
        self.redirect_with_context("/my", 
            flashmsg = ("Event created successfully, emails have been sent to guests", "ok"), 
            token = owner_token)

#class ChooseTimeslotsPage(BaseHandler):
#    URL = "/choose/(.+)"
#    
#    @logged_in
#    def post(self, owner_token):
#        evt = EventInfo.query(EventInfo.owner_token == owner_token).get() 
#        self.redirect_with_flashmsg("/my", "Event created successfully")





