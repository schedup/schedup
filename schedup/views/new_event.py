"""
Create new event flow
"""
import string
import random
from datetime import datetime
from schedup.base import BaseHandler, logged_in
from schedup.models import UserProfile, EventInfo, EventGuest


class NewEventPage(BaseHandler):
    URL = "/new"
    TOKEN_SIZE = 20
    
    @classmethod
    def generate_token(cls, chars = string.ascii_letters + string.digits):
        return ''.join(random.choice(chars) for _ in range(cls.TOKEN_SIZE))

    @logged_in
    def get(self):
        return self.render_response("new_event.html", post_url = self.URL)

    @logged_in
    def post(self):
        daytime = []
        if self.request.params.get("morning", "off") == "on":
            daytime.append("morning")
        if self.request.params.get("noon", "off") == "on":
            daytime.append("noon")
        if self.request.params.get("evening", "off") == "on":
            daytime.append("evening")
        guests = []
        for email in self.request.params["guests"].split(";"):
            user = UserProfile.query(UserProfile.email == email).get()
            if user:
                gst = EventGuest(user = user, token = self.generate_token())
            else:
                gst = EventGuest(email = email, token = self.generate_token())
            guests.append(gst)
        
        owner_token = self.generate_token()
        evt = EventInfo(owner = self.user.key, 
            owner_token = owner_token,
            title = self.request.params["title"],
            daytime = daytime,
            type = self.request.params.get("type"),
            start_window = datetime.strptime(self.request.params["fromdate"], "%Y-%m-%d"),
            end_window = datetime.strptime(self.request.params["todate"], "%Y-%m-%d"),
        )
        evt.put()
        
        return self.render_response("calendar.html", title = "Choose Time Slots", 
            post_url = "/choose/%s" % (owner_token,))


class ChooseTimeslotsPage(BaseHandler):
    URL = "/choose/(.+)"
    
    @logged_in
    def post(self, owner_token):
        evt = EventInfo.query(EventInfo.owner_token == owner_token).get() 
        self.session["flash"] = "Event Created"
        self.redirect("/my")





