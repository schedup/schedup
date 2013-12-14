"""
Create new event flow
"""
import logging
from dateutil.parser import parse as parse_datetime
from schedup.base import BaseHandler, logged_in
from schedup.models import UserProfile, EventInfo, EventGuest
from schedup.utils import send_email
try:
    from Crypto.Random import random
except ImportError:
    import random

def generate_random_token(length):
    return "".join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-") 
        for _ in range(length))


class NewEventPage(BaseHandler):
    URL = "/new"
    TOKEN_SIZE = 25
    
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
                gst = EventGuest(user = user.key, email = email, token = generate_random_token(self.TOKEN_SIZE))
            else:
                gst = EventGuest(email=email, token = generate_random_token(self.TOKEN_SIZE))
            guests.append(gst)
        if not guests:
            return self.redirect_with_flashmsg(self.URL, "No emails given", "error")
        
        title = self.request.params["title"]
        fromtime = parse_datetime(self.request.params["fromdate"])
        totime = parse_datetime(self.request.params["todate"])
        if fromtime > totime:
            return self.redirect_with_flashmsg(self.URL, "Start time is later than end time", "error")
        
        owner_token = generate_random_token(self.TOKEN_SIZE)
        evt = EventInfo(owner = self.user.key, 
            owner_token = owner_token,
            title = title,
            daytime = daytime,
            type = self.request.params.get("type"),
            start_window = fromtime,
            end_window = totime,
            guests = guests,
            description=self.request.params["description"],
            duration=int(float(self.request.params["slider-step"])*60),
        )
        evt.put()
        self.session["eventkey"] = evt.key.urlsafe()
        
        for guest in guests:
            send_email("%s invited you to %s" % (self.user.fullname, title),
                recipient = guest.email,
                html_body = self.render_template("emails/guest.html", 
                        fullname = self.user.fullname, title = title, token = guest.token),
            )
        
        logging.info("Guests: %r", guests)       
        self.redirect_with_flashmsg("/cal/%s" % (owner_token,), 
            msg = "Invites were sent to guests. Please vote", style = "ok")



    


    


