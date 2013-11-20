"""
Events I organize or that I am invited to
"""
from schedup.base import BaseHandler, logged_in


class MyEventsPage(BaseHandler):
    URL = "/my"
    
    @logged_in
    def get(self):
        self.render_response("event_list.html", events = self.user.get_owner_events(), owner = True)

class InvitedToPage(BaseHandler):
    URL = "/invited"
    
    @logged_in
    def get(self):
        self.render_response("event_list.html", events = self.user.get_participating_events(), owner = False)



