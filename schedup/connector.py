import json
from apiclient import discovery
from webapp2 import cached_property
        

class GoogleConnector(object):
    def __init__(self, oauth):
        self.oauth = oauth
    
    @cached_property
    def _calendar_service(self):
        return discovery.build('calendar', 'v3')

    @cached_property
    def user_info(self):
        return self.oauth.credentials.id_token
    
    @cached_property
    def user_email(self):
        return self.user_info["email"]
    
    def get_contacts(self, query, max_results):
        http = self.oauth.http()
        empty = {}
        headers, body = http.request("https://www.google.com/m8/feeds/contacts/default/full?"
            "alt=json&max-results=%d&q=%s" % (max_results, query), headers = {"GData-Version" : 3.0})
        if headers.status != 200:
            raise ValueError("Get profile failed", headers, body)

        by_email = {}
        for entry in json.loads(body)["feed"].get("entry", ()):
            if not "gd$email" in entry:
                continue
            title = entry.get("title", empty).get("$t")
            for email in entry["gd$email"]:
                addr = email.get("address")
                if not addr:
                    continue
                if not title:
                    title = addr
                if addr in by_email:
                    if query in title:
                        by_email[addr] = title
                    else:
                        continue
                by_email[addr] = title
            
        return [{"email" : email, "name" : name} for email, name in by_email.iteritems()]
    
    def list_calendars(self):
        return self._calendar_service.calendarList().list().execute(http = self.oauth.http())
    
    def get_events(self, calendar_id, start_date, end_date):
        entries = self._calendar_service.events().list(calendarId = calendar_id, 
            timeMin = start_date.strftime("%Y-%m-%dT00:00:00Z"), 
            timeMax = end_date.strftime("%Y-%m-%dT23:59:59Z")).execute(http = self.oauth.http())
        return entries["items"]
    
    def create_event(self, calendar_id, event_info):
        '''
        event_info = {
          'summary': 'Appointment',
          'location': 'Somewhere',
          'start': {
            'dateTime': '2011-06-03T10:00:00.000-07:00'
          },
          'end': {
            'dateTime': '2011-06-03T10:25:00.000-07:00'
          },
          'attendees': [
            {
              'email': 'attendeeEmail',
            },
          ],
        }
        '''
        return self._calendar_service.events().insert(calendarId=calendar_id, 
            body=event_info).execute(http = self.oauth.http())        
    
    def get_profile(self):
        headers, body = self.oauth.http().request("https://www.googleapis.com/oauth2/v2/userinfo?alt=json")
        if headers.status != 200:
            raise ValueError("Get profile failed", headers, body)
        return json.loads(body)




