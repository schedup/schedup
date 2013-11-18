import json
from apiclient import discovery
from gdata.contacts.client import ContactsClient, ContactsQuery
from gdata.gauth import ClientLoginToken
from webapp2 import cached_property
        

class GoogleConnector(object):
    def __init__(self, oauth):
        self.oauth = oauth
    
    @cached_property
    def _calendar_service(self):
        return discovery.build('calendar', 'v3')
    
    @cached_property
    def _contacts_client(self):
        return ContactsClient(source = "SchedUp", 
            auth_token = ClientLoginToken(self.oauth.credentials.access_token))

    @cached_property
    def user_info(self):
        return self.oauth.credentials.id_token
    
    @cached_property
    def user_email(self):
        return self.user_info["email"]
    
    def get_contacts(self):
        query = ContactsQuery(max_results = 10)
        return self._contacts_client.GetContacts(q=query)
    
    def list_calendars(self):
        return self._calendar_service.calendarList().list().execute(http = self.oauth.http())
    
    def get_events(self, calendarId, start_date, end_date):
        return self._calendar_service.events().list(calendarId=calendarId, timeMin = start_date, 
            timeMax = end_date).execute(http = self.oauth.http())
    
    def get_profile(self):
        headers, body = self.oauth.http().request("https://www.googleapis.com/oauth2/v2/userinfo?alt=json")
        if headers.status != 200:
            raise ValueError("Request failed - %s" % (headers,))
        return json.loads(body)




