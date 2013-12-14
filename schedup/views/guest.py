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
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        self.render_response("guest.html", post_url = "/guest/%s" % (token,), event = evt, 
            the_guest = guest, 
            flashmsg = "Event was canceled" if evt.status == "canceled" else None,
            flashclass = "error", 
            flashtimeout = -1)

    def post(self, token):
        evt, guest = EventInfo.get_by_guest_token(token)
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        guest.status = self.request.params.get("status")
        evt.put()
        if guest.user:
            url="/invited"
        else:
            url="/"
        return self.redirect_with_flashmsg(url, "Thank You!!", "ok")


class EditEventPage(BaseHandler):
    URL = "/edit/(.+)"
    
    @logged_in
    def get(self, owner_token):
        evt=EventInfo.query(EventInfo.owner_token==owner_token).get()
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        evt.voting_count = 0
        evt.decline_count = 0
        evt.put()
        self.render_response("edit.html",event = evt)

class SendEventPage(BaseHandler):
    URL = "/send/(.+)"
    
    @logged_in
    def get(self, owner_token):
        evt=EventInfo.query(EventInfo.owner_token==owner_token).get()
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        
        event_details = {
            'summary': evt.title,
            'description': evt.description,
            'location': '',
            'status':'confirmed',
            'start': {'dateTime': evt.start_time.isoformat() + "+02:00",},
            'end': {'dateTime': evt.end_time.isoformat() + "+02:00"},
            'attendees': [{'email': guest.email, 'responseStatus':'accepted'}
                for guest in evt.guests if guest.status == "accept"],
        }
        logging.info("log: event status = %r", evt.status)
        if (evt.status == "pending"):    
            evt.status="sent"
            event_details = {
                'summary': evt.title,
                'description': evt.description,
                'location': '',
                'status':'confirmed',
                'start': {'dateTime': evt.start_time.isoformat() + "+02:00",},
                'end': {'dateTime': evt.end_time.isoformat() + "+02:00"},
                'attendees': [{'email': guest.email, 'responseStatus':'accepted'}
                    for guest in evt.guests if guest.status == "accept"],
            }
            logging.info("evt=%r", event_details)
            resp = self.gconn.create_event("primary", event_details, send_notifications = True)
            logging.info("resp = %r", resp)
            evt.evtid = resp["id"]
            evt.put()
            return self.redirect_with_flashmsg("/my", "Invites sent", "ok")
        elif (evt.status == "sent"):
            resp = self.gconn.update_event("primary",evt.evtid, event_details, send_notifications = True)
            return self.redirect_with_flashmsg("/my", "Updates sent", "ok")

class CancelEventPage(BaseHandler):
    URL = "/cancel/(.+)"
    
    @logged_in
    def get(self, owner_token):
        evt=EventInfo.query(EventInfo.owner_token==owner_token).get()
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        evt.status = "canceled"
        evt.put()
        if evt.evtid:
            self.gconn.remove_event("primary", evt.evtid, send_notifications = True)
        self.redirect_with_flashmsg("/my", "Event '%s' canceled" % (evt.title,), "note")

class GuestDeclined(BaseHandler):
    URL = "/decline/(.+)"
    
    def get(self, token):
        evt, guest = EventInfo.get_by_guest_token(token)
        guest.status = "decline"
        evt.put()
        self.redirect_with_context("/my")


