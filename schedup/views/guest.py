"""
Guest flow (either logged in or not)
"""
from schedup.base import BaseHandler, logged_in
from schedup.models import EventInfo, EventGuest
import logging

class GuestPage(BaseHandler):
    URL = "/guest/(.+)"
    
    def get(self, token):
        evt, guest = EventInfo.get_by_guest_token(token)
        logging.info("evt=%r, guest=%r", evt, guest)
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!")
        self.render_response("guest.html", post_url = "/guest/%s" % (token,),event = evt)

    
    def post(self, token):
        evt, guest = EventInfo.get_by_guest_token(token)
        guest.status = self.request.params.get("status")
        evt.put()
        return self.redirect_with_flashmsg("/", "Thank You!!")

class EditEventPage(BaseHandler):
    URL = "/edit/(.+)"
    
    @logged_in
    def get(self, owner_token):
        self.render_response("layout.html", content = "edit event")





