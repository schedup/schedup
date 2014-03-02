"""
Create new event flow
"""
import logging
import json
from dateutil.parser import parse as parse_datetime
from schedup.base import BaseHandler, logged_in
from schedup.models import UserProfile, EventInfo, EventGuest
from schedup.utils import send_email
from schedup.facebook import generate_random_token, fb_logged_in
from schedup.connector import send_gcm_message
from datetime import datetime
from schedup.views.apis import EMAIL_PATTERN


class RedirectWithFlash(Exception):
    def __init__(self, url, msg, style):
        self.url = url
        self.msg = msg
        self.style = style

TOKEN_SIZE = 25

def create_or_update_event(self, evt, source):
    logging.info("params: %r", self.request.params)

    title = self.request.params["title"]
    location = self.request.params["where"]
    fromtime = parse_datetime(self.request.params["fromdate"]).date()
    totime = parse_datetime(self.request.params["todate"]).date()
    if fromtime > totime:
        raise RedirectWithFlash(self.URL, "Start time is later than end time", "error")

    if fromtime < datetime.now().date():
        raise RedirectWithFlash(self.URL, "Start time is in the past", "error")

    clear_votes = evt and (fromtime > evt.start_window or totime < evt.end_window)
    logging.info("clear_votes = %r", clear_votes)

    daytime = self.request.params.getall("when")
    guests = []    
    for email in self.request.params["guests"].split(";"):
        if source == "facebook":
            email, name = email.split("/", 1)
        else:
            name = None
            if not EMAIL_PATTERN.match(email):
                raise ValueError("Invalid email %r" % (email,))
        if evt:
            found = False
            for gst in evt.guests:
                if gst.email == email:
                    guests.append(gst)
                    found = True
                    if not gst.selected_times:
                        continue
                    gst.selected_times = [(s, e) for s, e in gst.selected_times
                        if s.date() >= fromtime and e.date() <= totime]
                    break
            if found:
                continue
        
        user = UserProfile.query(UserProfile.email == email).get()
        if not user:
            user = UserProfile.query(UserProfile.facebook_id == email).get()
            
        token = generate_random_token(TOKEN_SIZE)
        if user:
            gst = EventGuest(user = user.key, email = email, token = token, name = name)
        else:
            gst = EventGuest(email=email, token = token, name = name)
        logging.info("Guest token %r: %r", email, token)
        guests.append(gst)
    if not guests:
        raise RedirectWithFlash(self.URL, "No guests chosen", "error")
    
    if not evt:
        evt = EventInfo(owner_token = generate_random_token(TOKEN_SIZE), owner = self.user.key,
            first_owner_save = True, source = source)
    elif evt.owner_selected_times:
        evt.owner_selected_times = [(s, e) for s, e in evt.owner_selected_times
            if s.date() >= fromtime and e.date() <= totime]
    
    evt.title = title
    evt.location = location
    evt.daytime = daytime
    evt.status = "pending"
    evt.type = self.request.params.get("type")
    evt.start_window = fromtime
    evt.end_window = totime
    evt.start_time = None
    evt.end_time = None
    evt.guests = guests
    evt.description = self.request.params["description"]
    evt.duration = int(float(self.request.params["slider-step"])*60)
    evt.put()
    
    logging.info("evt = %r", evt)
    return evt


class NewEventPage(BaseHandler):
    URL = "/new"
    
    @logged_in
    def get(self):
        fake_event = {
            "title" : "", 
            "start_window" : None,
            "end_window" : None,
            "daytime" : ("evening",),
            "type" : "friends",
            "duration" : 120,
            "location" : "",
            "description" : "",
        }
        if not self.user.seen_tutorial1:
            self.user.seen_tutorial1 = True
            self.user.put()
            show_tutorial = True
        else:
            show_tutorial = False
        
        return self.render_response("new_event.html", post_url=self.URL, 
            the_event = fake_event, the_event_guests=[], edit_event = False, section = "new", which="google",
            show_tutorial = show_tutorial, today = datetime.now())

    @logged_in
    def post(self):
        try:
            evt = create_or_update_event(self, None, "google")
        except RedirectWithFlash as ex:
            return self.redirect_with_flashmsg(ex.url, ex.msg, ex.style)
        self.session["eventkey"] = evt.key.urlsafe()
        
        logging.info("Guests: %r", evt.guests)
        self.redirect("/cal/%s" % (evt.owner_token,)) 


class NewFBEventPage(BaseHandler):
    URL = "/fbnew"
    
    @fb_logged_in
    def get(self):
        fake_event = {
            "title" : "", 
            "start_window" : None,
            "end_window" : None,
            "daytime" : ("evening",),
            "type" : "friends",
            "duration" : 120,
            "location" : "",
            "description" : "",
        }
        return self.render_response("new_event.html", post_url=self.URL, 
            the_event = fake_event, the_event_guests=[], edit_event = False, section = "newfb", which = "facebook", today = datetime.now())

    @logged_in
    def post(self):
        try:
            logging.info("guests: %r", self.request.params["guests"])
            evt = create_or_update_event(self, None, "facebook")
        except RedirectWithFlash as ex:
            return self.redirect_with_flashmsg(ex.url, ex.msg, ex.style)
        self.session["eventkey"] = evt.key.urlsafe()
        
        logging.info("Guests: %r", evt.guests)
        self.redirect("/cal/%s" % (evt.owner_token,)) 


class EditEventPage(BaseHandler):
    URL = "/edit/(.+)"
    
    @logged_in
    def get(self, owner_token):
        evt=EventInfo.query(EventInfo.owner_token==owner_token).get()
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        
        self.render_response("new_event.html", 
            post_url = "/edit/%s" % (owner_token,),
            user_token = owner_token,
            the_event = evt,
            edit_event = True,
            the_event_guests = json.dumps([{"id":gst.email, "name":gst.fullname} for gst in evt.guests]),
            section=None,
        )
    
    @logged_in
    def post(self, owner_token):
        evt=EventInfo.query(EventInfo.owner_token==owner_token).get()
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")

        try:
            create_or_update_event(self, evt, None)
        except RedirectWithFlash as ex:
            return self.redirect_with_flashmsg(ex.url, ex.msg, ex.style)
        
        for guest in evt.guests:
            if evt.source == "google":
                send_email("%s updated %s" % (self.user.fullname, evt.title),
                    recipient = guest.email,
                    html_body = self.render_template("emails/update.html", 
                            fullname = self.user.fullname, title = evt.title, token = guest.token,
                            location = evt.location, description = evt.description)
                )
            elif self.fbconn:
                self.fbconn.send_message(guest.email,
                    "%s invited you to %s" % (self.user.fullname, evt.title), 
                    self.render_template("emails/new.html", fullname = self.user.fullname, 
                        title = evt.title, token = guest.token)
                )
            
            if guest.user:
                gcm_id = guest.user.get().gcm_id
                if gcm_id:
                    send_gcm_message(gcm_id, evt.title, "%s updated the event" % (self.user.fullname,))
        
        logging.info("Guests: %r", evt.guests)
        self.redirect_with_flashmsg("/cal/%s" % (evt.owner_token,), 
            msg = "Event info updated", style = "ok")        





    


