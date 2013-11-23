"""
Events I organize or that I am invited to
"""
from schedup.base import BaseHandler, logged_in
from schedup.models import EventInfo


class MyEventsPage(BaseHandler):
    URL = "/my"
    
    @logged_in
    def get(self):
        token = self.session.pop("token", None)
        self.render_response("event_list.html", 
            owner = True,
            events = self.user.get_owner_events().order(-EventInfo.created_at),
            token = token, 
        )

class InvitedToPage(BaseHandler):
    URL = "/invited"
    
    @logged_in
    def get(self):
        self.render_response("event_list.html", events = self.user.get_participating_events(), owner = False)





