"""
APIs for the client-side:
 * Get contacts starting with XXX
 * Get events for time range
 * Get other people's time slots
"""
from schedup.base import BaseHandler, api_call, logged_in, maybe_logged_in
from datetime import datetime, timedelta
import json
import re

EMAIL_PATTERN = re.compile(r".+?@.+?\..+")


DAY = timedelta(days=1)

class GetUserContacts(BaseHandler):
    URL = "/api/get-contacts"
    
    @logged_in
    @api_call(q = unicode, max_results = int)
    def get(self, q, max_results = 10):
        return self.gconn.get_contacts(q, max_results = max_results)

class AutocompleteContacts(BaseHandler):
    URL = "/api/autocomplete-contacts"
    
    @logged_in
    def get(self):
        q = self.request.params["q"]
        results = []
        if EMAIL_PATTERN.match(q):
            results.append({"id" : q, "name" : q})
        for res in self.gconn.get_contacts(q, 10):
            name = res["name"]
            if not EMAIL_PATTERN.match(name):
                name += " &lt;%s&gt;" % (res["email"],)
            results.append({"id" : res["email"], "name" : name})
        
        json_data = json.dumps(results)
        self.response.content_type = 'application/json'
        self.response.write(json_data)


class GetUserCalendaer(BaseHandler):
    URL = "/api/get-calendar"
    
    @logged_in
    @api_call(calid = str, weeks_from_now = int)
    def get(self, calid = "primary", weeks_from_now = 1):
        now = datetime.now()
        return self.gconn.get_events(calid, now, now + weeks_from_now * 7 * DAY)

class GetUserCalendaerList(BaseHandler):
    URL = "/api/get-calendar-list"
    
    @logged_in
    @api_call()
    def get(self):
        return [{"id":cal["id"], "name":cal["summary"], "timezone" : cal["timeZone"]}
            for cal in self.gconn.list_calendars()["items"] 
                if not cal.get("hidden", False)]

class GetEventTimeslots(BaseHandler):
    URL = "/api/get-event-slots"
    
    @maybe_logged_in
    @api_call(user_token = str)
    def get(self, user_token):
        pass





