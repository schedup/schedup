import json
from apiclient import discovery
from gdata.contacts.client import ContactsClient, ContactsQuery
from gdata.gauth import ClientLoginToken
        

class GoogleConnector(object):
    def __init__(self, oauth):
        self.oauth = oauth
        self._calendar_service = discovery.build('calendar', 'v3')
        self._contacts_client = ContactsClient(source = "SchedUp", 
            auth_token = ClientLoginToken(self.oauth.credentials.access_token))
    
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
        return json.loads(body)




