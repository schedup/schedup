"""
Guest flow (either logged in or not)
"""
import logging
from schedup.base import BaseHandler, logged_in
from schedup.models import EventInfo


class GuestPage(BaseHandler):
    URL = "/guest/(.+)"
    
    def get(self, token):
        evt, guest = EventInfo.get_by_guest_token(token)
        logging.info("evt=%r, guest=%r", evt, guest)
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!")
        self.render_response("guest.html", post_url = "/guest/%s" % (token,), event = evt)

    def post(self, token):
        evt, guest = EventInfo.get_by_guest_token(token)
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        guest.status = self.request.params.get("status")
        evt.put()
        return self.redirect_with_flashmsg("/", "Thank You!!", "ok")


class EditEventPage(BaseHandler):
    URL = "/edit/(.+)"
    
    @logged_in
    def get(self, owner_token):
        evt=EventInfo.query(EventInfo.owner_token==owner_token).get()
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        self.render_response("edit.html",event = evt)





