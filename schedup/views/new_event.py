"""
Create new event flow
"""
import logging
import json
from dateutil.parser import parse as parse_datetime
from schedup.base import BaseHandler, logged_in
from schedup.models import UserProfile, EventInfo, EventGuest
from schedup.utils import send_email
from schedup.facebook import generate_random_token


class RedirectWithFlash(Exception):
    def __init__(self, url, msg, style):
        self.url = url
        self.msg = msg
        self.style = style

TOKEN_SIZE = 25

def create_or_update_event(self, evt):
    logging.info("params: %r", self.request.params)

    title = self.request.params["title"]
    location = self.request.params["where"]
    fromtime = parse_datetime(self.request.params["fromdate"]).date()
    totime = parse_datetime(self.request.params["todate"]).date()
    if fromtime > totime:
        raise RedirectWithFlash(self.URL, "Start time is later than end time", "error")

    clear_votes = evt and (fromtime > evt.start_window or totime < evt.end_window)
    logging.info("clear_votes = %r", clear_votes)
    daytime = self.request.params.getall("when")
    guests = []    
    for email in self.request.params["guests"].split(";"):
        if evt:
            found = False
            for gst in evt.guests:
                if gst.email == email:
                    guests.append(gst)
                    found = True
                    if clear_votes:
                        gst.selected_times = None
                    break
            if found:
                continue
        
        user = UserProfile.query(UserProfile.email == email).get()
        token = generate_random_token(TOKEN_SIZE)
        if user:
            gst = EventGuest(user = user.key, email = email, token = token)
        else:
            gst = EventGuest(email=email, token = token)
        logging.info("Guest token %r: %r", email, token)
        guests.append(gst)
    if not guests:
        raise RedirectWithFlash(self.URL, "No emails given", "error")
    
    if not evt:
        evt = EventInfo(owner_token = generate_random_token(TOKEN_SIZE), owner = self.user.key,
            first_owner_save = True)
    
    if clear_votes:
        evt.owner_selected_times = None
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
        return self.render_response("new_event.html", post_url=self.URL, 
            the_event = fake_event, the_event_guests=[], edit_event = False, section="new")

    @logged_in
    def post(self):
        try:
            evt = create_or_update_event(self, None)
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





    


