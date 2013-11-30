"""
Create new event flow
"""
import string
import random
from dateutil.parser import parse as parse_datetime, parse
from datetime import timedelta, date
from schedup.base import BaseHandler, logged_in, maybe_logged_in
from schedup.models import UserProfile, EventInfo, EventGuest
from schedup.utils import send_email
from google.appengine.ext import ndb
import logging
import json


class NewEventPage(BaseHandler):
    URL = "/new"
    TOKEN_SIZE = 20
    
    @classmethod
    def generate_token(cls, chars=string.ascii_letters + string.digits):
        return ''.join(random.choice(chars) for _ in range(cls.TOKEN_SIZE))

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
                gst = EventGuest(user = user.key, email = email, token = self.generate_token())
            else:
                gst = EventGuest(email=email, token=self.generate_token())
            guests.append(gst)
        if not guests:
            return self.redirect_with_flashmsg("/new", "No emails given", "error")
        
        title = self.request.params["title"]
        fromtime = parse_datetime(self.request.params["fromdate"])
        totime = parse_datetime(self.request.params["todate"])
        if fromtime > totime:
            return self.redirect_with_flashmsg("/new", "Start time is later than end time", "error")
        
        owner_token = self.generate_token()
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
        # hack for the first milestone {{
        evt.start_time = evt.start_window
        if "morning" in daytime:
            evt.start_time += timedelta(hours = 8)
        elif "noon" in daytime:
            evt.start_time += timedelta(hours = 12)
        else:
            evt.start_time += timedelta(hours = 20)
        evt.end_time = evt.start_time + timedelta(hours = 2)
        # }}
        evt.put()
        # clear the cache so /my will show this event
        ndb.get_context().clear_cache()
        
        for guest in guests:
            send_email("%s invited you to %s" % (self.user.fullname, title),
                recipient = guest.email,
                html_body = self.render_template("emails/guest.html", 
                        fullname = self.user.fullname, title = title, token = guest.token),
            )
        
        logging.info("Guests: %r", guests)
        
        self.redirect_with_context("/choose/" + owner_token , 
            flashmsg = "Invites for voting sent, Please Vote",
            flashclass = "ok", 
            token = owner_token)


class ChooseTimeslotsPage(BaseHandler):
    URL = "/choose/(.+)"
    
    @maybe_logged_in
    def get(self, owner_token):
        the_event = EventInfo.get_by_owner_token(owner_token)
        if not the_event:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        
        days = []
        s = the_event.start_window
        while s <= the_event.end_window:
            days.append((s.day, ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"][s.weekday()]))
            s += timedelta(days=1)

        hours = set()
        if "morning" in the_event.daytime:
            hours.update(range(8,13))
        if "noon" in the_event.daytime:
            hours.update(range(12,17))
        if "evening" in the_event.daytime:
            hours.update(range(17,24))
        hours = range(min(hours), max(hours)+1)
        
        logging.info("hours = %r", hours)
        
        timemap = {}
        for gst in the_event.guests:
            for ts, duration in (gst.selected_times if gst.selected_times else ()):
                for halfhour in range(duration // 30):
                    k = ts + timedelta(minutes=halfhour * 30)
                    if k not in timemap:
                        timemap[k] = 0
                    timemap[k] += 1
        
        suggested = []
        #count = len(the_event.guests)+1
        #for slot, count in timemap.items():
        #    suggested.append({"going" : slot,
        #        "count" : count,
        #        "day":5,
        #        "hour":6,
        #        "duration":1.5,
        #        })
        
        events = []
        if self.user:
            for evt in self.gconn.get_events("primary", the_event.start_window, the_event.end_window):
                start = parse(evt["start"]["dateTime"])
                end = parse(evt["end"]["dateTime"])
                events.append({
                    "title" : evt["summary"], 
                    "day" : (start.date() - the_event.start_window).days,
                    "hour" : start.hour + start.minute / 60.0, 
                    "duration" : (end - start).total_seconds() / (60*60.0),
                })
        
        self.render_response("calendar2.html", days = days, hours = hours, 
            events_json = json.dumps(events), min_hour = min(hours),
            suggested_json = json.dumps(suggested),
            title = the_event.title,
            post_url = "/choose/%s" % (owner_token,),
        )
    
    def post(self, owner_token):
        selected = json.loads(self.request.body)
        logging.info("selected=%r", selected)

        the_event = EventInfo.get_by_owner_token(owner_token)
        the_event.owner_selected_times = selected
        the_event.put()
        
        res = ""
        json_data = json.dumps(res)
        self.response.content_type = "application/json"
        self.response.write(json_data)


class ChooseTimeslotsPageForGuest(BaseHandler):
    URL = "/guestChoose/(.+)"
    
    def get(self, token):
        pass
    
    
    
class CalendarTest(BaseHandler):
    URL = "/cal"

    def get(self):
        days = []
        today = date.today()
        for d in range(7):
            d = today + timedelta(days = d)
            days.append({"date" : d.strftime("%d %b"), "index" : d.toordinal(),
                "weekday":["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"][d.weekday()]})
        
        self.render_response("calendar2.html", 
            days = days,
            hours=[8,9,10,11,12])
    



