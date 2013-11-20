"""
Guest flow (either logged in or not)
"""
from schedup.base import BaseHandler, logged_in
from schedup.models import EventInfo


class GuestPage(BaseHandler):
    URL = "/guest/(.+)"
    
    def get(self, token):
        evt, guest = EventInfo.get_by_guest_token(token)
        if not evt:
            self.redirect_with_flashmsg("/", "Invalid token!")
        self.render_response("calendar.html", post_url = "/guest/%s" % (token,))
    
    def post(self, token):
        pass


class EditEventPage(BaseHandler):
    URL = "/edit/(.+)"
    
    @logged_in
    def get(self, owner_token):
        self.render_response("layout.html", content = "edit event")





