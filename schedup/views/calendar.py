import json
import logging
from datetime import timedelta, datetime
from email.utils import parseaddr
from dateutil.parser import parse
from schedup.models import EventInfo
from schedup.base import BaseHandler, maybe_logged_in


class CalendarPage(BaseHandler):
    URL = "/cal/(.+)"
    
    @maybe_logged_in
    def get(self, user_token):
        is_owner, the_event, user = EventInfo.get_by_token(user_token)
        if not the_event:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        
        days = []
        s = the_event.start_window
        while s <= the_event.end_window:
            days.append({"date" : s.strftime("%d %b"), "index" : s.toordinal(),
                "weekday":["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"][s.weekday()]})
            s += timedelta(days = 1)
        
        hours = set()
        if "morning" in the_event.daytime:
            hours.update(range(7,12))
        if "noon" in the_event.daytime:
            hours.update(range(12,17))
        if "afternoon" in the_event.daytime:
            hours.update(range(14,20))
        if "evening" in the_event.daytime:
            hours.update(range(17,23))
        hours = range(min(hours), max(hours)+1)
        
        if self.gconn:
            user_calendar_events = []
            try:
                goog_events = self.gconn.get_events("primary", the_event.start_window, the_event.end_window)
            except Exception:
                goog_events = ()
            for evt in goog_events:
                start = parse(evt["start"]["dateTime"])
                end = parse(evt["end"]["dateTime"])
                user_calendar_events.append({
                    "title" : evt["summary"], 
                    "start" : start,
                    "end" : end,
                })
        else:
            user_calendar_events = ()
        
        user_calendar_votes= []
        for gst in the_event.guests:
            if gst.email == user.email:
                continue
            if not gst.selected_times:
                continue
            for start_time, end_time in gst.selected_times:
                user_calendar_votes.append({
                    "start" : start_time, 
                    "end" : end_time, 
                    "user" : self.canonize_email(gst.email)
                })
        
        user_selected_slots = []
        if is_owner:
            ranges = the_event.owner_selected_times
        else:
            ranges = user.selected_times
            if the_event.owner_selected_times:
                for start_time, end_time in the_event.owner_selected_times:
                    user_calendar_votes.append({
                        "start" : start_time, 
                        "end" : end_time, 
                        "user" : self.canonize_email(gst.email)
                    })
        
        if ranges:
            for start_time, end_time in ranges:
                first = start_time.hour * 2 + (start_time.minute != 0)
                for hh in range(int((end_time - start_time).total_seconds() // (30 * 60))):
                    user_selected_slots.append({
                        "day" : start_time.toordinal(), 
                        "halfhour" : first + hh, 
                    })
        
        self.render_response("calendar2.html", 
            days = days,
            hours = hours,
            user_token = user_token,
            user_calendar_events = json.dumps(self.process_events(user_calendar_events, min(hours))),
            user_calendar_votes = json.dumps(self.process_events(user_calendar_votes, min(hours))),
            user_selected_slots = json.dumps(user_selected_slots),
            post_url = "/cal/%s" % (user_token,),
            the_event = the_event,
            is_owner = is_owner,
        )

    @staticmethod
    def canonize_email(email):
        _, addr = parseaddr(email)
        return addr.replace(".", "_").replace("+", "_").replace("-", "_").replace("@", "_")
    
    @staticmethod
    def process_events(eventlist, min_hour):
        processed = []
        for evt in eventlist:
            s = evt["start"]
            e = evt["end"]
            if s.date() != e.date():
                continue
            evt2 = {
                "title" : evt.get("title"), 
                "start_day" : s.toordinal(), 
                "hour_offset" : (s - s.replace(hour = min_hour, minute=0, second=0, microsecond=0)).total_seconds() / 3600.0,
                "duration" : (e - s).total_seconds() / 3600.0,
                "user" : evt.get("user", ""),
            }
            processed.append(evt2)
        return processed
    
    @maybe_logged_in
    def post(self, user_token):
        is_owner, the_event, user = EventInfo.get_by_token(user_token)
        if not the_event:
            self.response.status = 403
            self.session["flashmsg"] = "Invalid token"
            self.session["flashclass"] = "error"
            return
    
        selected = json.loads(self.request.body)
        selected.sort()
        logging.info("selected=%r", selected)
        
        ranges = []
        start = None
        prev = {"day":None, "halfhour":None}
        for sel in selected:
            if not (prev["day"] == sel["day"] and prev["halfhour"] == sel["halfhour"] - 1):
                if start:
                    start_ts = datetime.fromordinal(start["day"]) + timedelta(minutes = 30 * start["halfhour"])
                    end_ts = datetime.fromordinal(start["day"]) + timedelta(minutes = 30 * (prev["halfhour"] + 1))
                    ranges.append((start_ts, end_ts))
                start = sel
            prev = sel
        if start:
            start_ts = datetime.fromordinal(start["day"]) + timedelta(minutes = 30 * start["halfhour"])
            end_ts = datetime.fromordinal(start["day"]) + timedelta(minutes = 30 * (prev["halfhour"]+1))
            ranges.append((start_ts, end_ts))
        logging.info("ranges=%r", ranges)
    
        if is_owner:
            the_event.owner_selected_times = ranges
        else:
            user.selected_times = ranges
        the_event.put()
    
        self.session["flashmsg"] = "Thanks for voting"
        self.session["flashclass"] = "ok"
    
        self.response.content_type = "application/json"
        if is_owner:
            url = "/my"
        elif user.user:
            url = "/invited"
        else:
            url = "/"
        self.response.write(json.dumps(url))
    

class DeclinePage(BaseHandler):
    URL = "/decline/(.+)"
    
    def get(self, user_token):
        is_owner, the_event, user = EventInfo.get_by_token(user_token)
        if not the_event:
            return self.redirect_with_flashmsg("/", "Invalid token!", "error")
        
        if is_owner:
            the_event.status = "canceled" 
            msg = "Event '%s' canceled" % (the_event.title,)
        else:
            user.status = "decline"
            user.selected_times = []
            msg = "You've declined '%s'" % (the_event.title,)
        the_event.put()
        if the_event.evtid:
            self.gconn.remove_event("primary", the_event.evtid, send_notifications = True)

        return self.redirect_with_flashmsg("/", msg, "note")






