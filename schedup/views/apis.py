"""
APIs for the client-side:
 * Get contacts starting with XXX
 * Get events for time range
 * Get other people's time slots
"""
import re
from schedup.base import BaseHandler, logged_in, json_handler, maybe_logged_in
from datetime import datetime, timedelta
from schedup.facebook import fb_logged_in
import logging
import json

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


class GCMRegisterClientID(BaseHandler):
    URL = "/api/gcmreg/(.+)"
    
    @logged_in
    def get(self, regid):
        if not regid or not regid.strip():
            self.response.status = 403
            return
        
        if self.user.gcm_id != regid:
            logging.info("%r: setting GCM regid %r", self.user.email, regid);
            self.user.gcm_id = regid
            self.user.put()
        
        self.response.content_type = "application/json"
        self.response.write(json.dumps("ok"))

class GCMTest(BaseHandler):
    URL = "/api/testgcm/(.+)"
    
    @logged_in
    def get(self, msg):
        if not self.user.gcm_id:
            return "no GCM regid"
        
        from schedup.connector import send_gcm_message
        return send_gcm_message(self.user.gcm_id, "test", msg)



