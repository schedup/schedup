"""
Create new event flow
"""
import logging
from dateutil.parser import parse as parse_datetime
from schedup.base import BaseHandler, logged_in
from schedup.models import UserProfile, EventInfo, EventGuest
from schedup.utils import send_email
import json
try:
    from Crypto.Random import random
except ImportError:
    import random


class RedirectWithFlash(Exception):
    def __init__(self, url, msg, style):
        self.url = url
        self.msg = msg
        self.style = style

TOKEN_SIZE = 25

def generate_random_token(length):
    return "".join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-") 
        for _ in range(length))

def create_or_update_event(self, evt):
    logging.info("params: %r", self.request.params)

    daytime = self.request.params.getall("when")
    guests = []    
    for email in self.request.params["guests"].split(";"):
        if evt:
            found = False
            for gst in evt.guests:
                if gst.email == email:
                    guests.append(gst)
                    found = True
                    gst.selected_times = None
                    break
            if found:
                continue
        
        user = UserProfile.query(UserProfile.email == email).get()
        if user:
            gst = EventGuest(user = user.key, email = email, token = generate_random_token(TOKEN_SIZE))
        else:
            gst = EventGuest(email=email, token = generate_random_token(TOKEN_SIZE))
        guests.append(gst)
    if not guests:
        raise RedirectWithFlash(self.URL, "No emails given", "error")
    
    title = self.request.params["title"]
    fromtime = parse_datetime(self.request.params["fromdate"])
    totime = parse_datetime(self.request.params["todate"])
    if fromtime > totime:
        raise RedirectWithFlash(self.URL, "Start time is later than end time", "error")
    
    if not evt:
        evt = EventInfo(owner_token = generate_random_token(TOKEN_SIZE), owner = self.user.key)
    
    evt.owner_selected_times = None
    evt.title = title
    evt.daytime = daytime
    evt.type = self.request.params["type"]
    evt.start_window = fromtime
    evt.end_window = totime
    evt.guests = guests
    evt.description = self.request.params["description"]
    evt.duration = int(float(self.request.params["slider-step"])*60)
    evt.put()
    
    logging.info("evt = %r", evt)
    return evt


class NewEventPage(BaseHandler):
    URL = "/new"
    TOKEN_SIZE = 25
    
    @logged_in
    def get(self):
        fake_event = {
            "title" : "", 
            "start_window" : None,
            "end_window" : None,
            "daytime" : ("evening",),
            "type" : "friends",
            "duration" : 120,
            "description" : "",
        }
        return self.render_response("new_event.html", post_url=self.URL, 
            the_event = fake_event, the_event_guests=[], edit_event = False)

    @logged_in
    def post(self):
        try:
            evt = create_or_update_event(self, None)
        except RedirectWithFlash as ex:
            return self.redirect_with_flashmsg(ex.url, ex.msg, ex.style)
        self.session["eventkey"] = evt.key.urlsafe()
        
        for guest in evt.guests:
            send_email("%s invited you to %s" % (self.user.fullname, evt.title),
                recipient = guest.email,
                html_body = self.render_template("emails/new.html", 
                        fullname = self.user.fullname, title = evt.title, token = guest.token),
            )
        
        logging.info("Guests: %r", evt.guests)
        self.redirect_with_flashmsg("/cal/%s" % (evt.owner_token,), 
            msg = "Invites were sent to guests. Please pick you time slots", style = "ok")


class EditEventPage(BaseHandler):
    URL = "/edit/(.+)"
    
    @logged_in
    def get(self, owner_token):
        evt=EventInfo.query(EventInfo.owner_token==owner_token).get()
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        
        self.render_response("new_event.html", 
            post_url = "/edit/%s" % (owner_token,),
            the_event = evt,
            edit_event = True,
            the_event_guests = json.dumps([{"id":gst.email, "name":gst.fullname} for gst in evt.guests])
        )
    
    @logged_in
    def post(self, owner_token):
        evt=EventInfo.query(EventInfo.owner_token==owner_token).get()
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")

        try:
            create_or_update_event(self, evt)
        except RedirectWithFlash as ex:
            return self.redirect_with_flashmsg(ex.url, ex.msg, ex.style)
        
        for guest in evt.guests:
            send_email("%s updated %s" % (self.user.fullname, evt.title),
                recipient = guest.email,
                html_body = self.render_template("emails/update.html", 
                        fullname = self.user.fullname, title = evt.title, token = guest.token),
            )
        
        logging.info("Guests: %r", evt.guests)
        self.redirect_with_flashmsg("/cal/%s" % (evt.owner_token,), 
            msg = "Event info updated", style = "ok")        





    


