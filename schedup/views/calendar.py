import re
import json
from datetime import timedelta
from email.utils import parseaddr
from dateutil.parser import parse
from schedup.models import EventInfo
import logging


def generate_calendar(self, user_token, post_url):
    is_owner, the_event, _ = EventInfo.get_by_token(user_token)
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
    if the_event.owner_selected_times:
        for start_time, end_time in the_event.owner_selected_times:
            user_calendar_votes.append({
                "start" : start_time, 
                "end" : end_time, 
                "user" : canonize_email(the_event.owner.email)
            })
    for gst in the_event.guests:
        if not gst.selected_times:
            continue
        for start_time, end_time in gst.selected_times:
            user_calendar_votes.append({
                "start" : start_time, 
                "end" : end_time, 
                "user" : canonize_email(gst.email)
            })
    
    self.render_response("calendar2.html", 
        days = days,
        hours = hours,
        user_token = user_token,
        user_calendar_events = json.dumps(_process_events(user_calendar_events, min(hours))),
        user_calendar_votes = json.dumps(_process_events(user_calendar_votes, min(hours))),
        post_url = post_url,
    )

email_address = re.compile(r"(\S+@\S+\.\S+)")

def canonize_email(email):
    _, addr = parseaddr(email)
    return addr.replace(".", "_").replace("+", "_").replace("-", "_").replace("@", "_")

def _process_events(eventlist, min_hour):
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

def handle_calendar_response(self, user_token, redirect_url):
    is_owner, the_event, _ = EventInfo.get_by_token(user_token)
    if not the_event:
        self.response.status = 403
        return

    selected = json.loads(self.request.body)
    logging.info("selected=%r", selected)

    self.response.content_type = "application/json"
    self.response.write(json.dumps(redirect_url))









