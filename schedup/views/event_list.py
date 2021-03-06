"""
Events I organize or that I am invited to
"""
from schedup.base import BaseHandler, logged_in
from schedup.models import EventInfo
from datetime import datetime, timedelta
from schedup.facebook import fb_logged_in


class MyEventsPage(BaseHandler):
    URL = "/my"
    
    @logged_in
    def get(self):
        token = self.session.pop("token", None)
        mintime = datetime.now() - timedelta(days = 3)
        self.render_response("event_list.html", 
            title = "My Events",
            owner = True,
            events = [evt for evt in 
                self.user.get_owner_events().filter(EventInfo.end_window >= mintime).order(EventInfo.end_window) 
                if evt.status != "canceled" and (not evt.end_time or evt.end_time >= mintime)],
            token = token,
            section="my",
        )

class MyFBEventsPage(BaseHandler):
    URL = "/fbmy"
    
    @fb_logged_in
    def get(self):
        return self.redirect("/my")


class InvitedToPage(BaseHandler):
    URL = "/invited"
    
    @logged_in
    def get(self):
        mintime = datetime.now() - timedelta(days = 3)
        
        events_cal = [evt for evt in 
                self.user.get_participating_events().filter(EventInfo.end_window >= mintime).order(EventInfo.end_window) 
                if evt.status != "canceled" and (not evt.end_time or evt.end_time >= mintime)]
        
        events_fb = [evt for evt in 
                self.user.get_participating_events_fb().filter(EventInfo.end_window >= mintime).order(EventInfo.end_window) 
                if evt.status != "canceled" and (not evt.end_time or evt.end_time >= mintime)]
        
        
        
        self.render_response("event_list.html", 
            title = "Invited To", 
            events = events_cal + events_fb,
            owner = False,
            section="invited",
        )





