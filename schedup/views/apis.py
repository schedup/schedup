"""
APIs for the client-side:
 * Get contacts starting with XXX
 * Get events for time range
 * Get other people's time slots
"""
import re
from schedup.base import BaseHandler, logged_in, json_handler
from datetime import datetime, timedelta
from schedup.facebook import fb_logged_in
import logging

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
        try:
            goog_results = self.gconn.get_contacts(q, 10)
        except Exception:
            goog_results = ()
        for res in goog_results:
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
        return self.gconn.get_events("primary", now, now + timedelta(days=14))


class FBAutocompleteContacts(BaseHandler):
    URL = "/api/fb-autocomplete-contacts"

    @fb_logged_in
    @json_handler
    def get(self):
        logging.info("in fb-autocomplete-contacts")
        return self.fbconn.get_friends(self.request.params["q"], 10)



