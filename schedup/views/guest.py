"""
Guest flow (either logged in or not)
"""
import logging
from dateutil.parser import parse as parse_datetime, parse
from datetime import timedelta, datetime
from schedup.utils import send_email
from google.appengine.ext import ndb
from schedup.base import BaseHandler, logged_in
from schedup.models import EventInfo, UserProfile, EventGuest


class GuestPage(BaseHandler):
    URL = "/guest/(.+)"
    
    def get(self, token):
        evt, guest = EventInfo.get_by_guest_token(token)
        logging.info("evt=%r, guest=%r", evt, guest)
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        self.render_response("guest.html", post_url = "/guest/%s" % (token), event = evt, 
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
        
#         if (evt.voting_count != 0):
#             self.redirect_with_flashmsg("/edit/" + owner_token, "you have %r new votes!" %evt.voting_count)
#         if (evt.voting_count != 0):
#             self.redirect_with_flashmsg("/edit/" + owner_token, "you have %r new declines!" %evt.decline_count)
        

        self.render_response("edit.html", post_url = "/edit/" + owner_token, event = evt)
        evt.new_notifications = 0
        evt.put()
    
    @logged_in    
    def post(self, owner_token):
        evt=EventInfo.query(EventInfo.owner_token==owner_token).get()
        
        if not evt:
            return self.redirect("/", "Invalid token!", "error")
        
        logging.info("self.request.params.has_key('when') = %r", self.request.params.has_key("when"))
        if self.request.params.has_key("when"):
            daytime = self.request.params.getall("when")
            logging.info("entered if, daytime = %r", daytime)
            logging.info("before, evt.daytime = %r", evt.daytime)
            evt.daytime = daytime
            logging.info("after, evt.daytime = %r", evt.daytime)
            evt.put()

        logging.info("self.request.params.get('title') instance: %r", type(self.request.params.get("title")))
        if self.request.params.has_key("title"):
            
            title = self.request.params["title"]
            logging.info("enterd if, title = %r", title)
            logging.info("before, evt.title = %r", evt.title)
            evt.title = title
            logging.info("after, evt.title = %r", evt.title)
            evt.put()

        if self.request.params.has_key("description"):
            description=self.request.params.get("description")
            evt.description = description
            evt.put()
        
        if self.request.params.has_key("slider-step"):
            duration=int(float(self.request.params.get("slider-step"))*60)
            evt.duration = duration
            evt.put()

        evt.put()
        # clear the cache so /my will show this event
        #ndb.get_context().clear_cache()
        
        self.redirect_with_context("/edit/" + owner_token, 
            flashmsg = "Updated",
            flashclass = "ok", 
            token = owner_token)

#         guests = []
#         for email in self.request.params["guests"].split(";"):
#             user = UserProfile.query(UserProfile.email == email).get()
#             if user:
#                 gst = EventGuest(user = user.key, email = email, token = self.generate_token())
#             else:
#                 gst = EventGuest(email=email, token=self.generate_token())
#             guests.append(gst)
#         if not guests:
#             return self.redirect_with_flashmsg("/new", "No emails given", "error")

#         fromtime = parse_datetime(self.request.params["fromdate"])
#         totime = parse_datetime(self.request.params["todate"])
#         if fromtime > totime:
#             return self.redirect_with_flashmsg("/new", "Start time is later than end time", "error")
        

#         evt = EventInfo(owner = self.user.key, 
#             owner_token = owner_token,
#             title = title,
#             daytime = daytime,
#             type = self.request.params.get("type"),
#             start_window = fromtime,
#             end_window = totime,
#             guests = guests,
#             description=self.request.params["description"],
#             duration=int(float(self.request.params["slider-step"])*60),
#         )

#         # hack for the first milestone {{
#         evt.start_time = evt.start_window
#         if "morning" in daytime:
#             evt.start_time += timedelta(hours = 8)
#         elif "noon" in daytime:
#             evt.start_time += timedelta(hours = 12)
#         else:
#             evt.start_time += timedelta(hours = 20)
#         evt.end_time = evt.start_time + timedelta(hours = 2)
#         # }}
        
#         for guest in guests:
#             send_email("%s invited you to %s" % (self.user.fullname, title),
#                 recipient = guest.email,
#                 html_body = self.render_template("emails/guest.html", 
#                         fullname = self.user.fullname, title = title, token = guest.token),
#             )
#         
#         logging.info("Guests: %r", guests)
#         
#         self.redirect_with_context("/choose/" + owner_token , 
#             flashmsg = "Invites for voting sent, Please Vote",
#             flashclass = "ok", 
#             token = owner_token)

class SendEventPage(BaseHandler):
    URL = "/send/(.+)"
    
    @logged_in
    def get(self, owner_token):
        evt=EventInfo.query(EventInfo.owner_token==owner_token).get()
        if not evt:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        
        final_time = self.request.params.get("radio-view");
        evt.start_time=datetime.strptime(str(final_time),'%Y-%m-%d %H:%M:%S');
        evt.end_time=evt.start_time+timedelta(hours=2);
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


