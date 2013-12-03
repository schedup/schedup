"""
APIs for the client-side:
 * Get contacts starting with XXX
 * Get events for time range
 * Get other people's time slots
"""
import re
from schedup.base import BaseHandler, logged_in, json_handler
from datetime import datetime, timedelta

EMAIL_PATTERN = re.compile(r".+?@.+?\..+")


class AutocompleteContacts(BaseHandler):
    URL = "/api/autocomplete-contacts"

    @logged_in
    @json_handler
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
        return results


class GetCalendarEvents(BaseHandler):
    URL = "/api/get-calendar"

    @logged_in
    @json_handler
    def get(self):
        now = datetime.now()
        return self.gconn.get_events("primary", now, now + timedelta(days=7))





