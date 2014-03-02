import functools
from schedup.base import BaseHandler, ON_DEV
from schedup import settings
import logging
import urllib2
import urllib
import urlparse
import json
from schedup.models import UserProfile
from schedup.utils import generate_random_token
from dateutil.parser import parse as parse_datetime
from datetime import timedelta


FB_SCOPES = "email,create_event,rsvp_event,user_events,manage_notifications,publish_stream"

if ON_DEV:
    FB_URI = "http://localhost:9080/fboauth"
else:
    FB_URI = "http://sched-up.appspot.com/fboauth"


def fb_logged_in(method):
    @functools.wraps(method)
    def method2(self, *args):
        fb_email = self.session.get("fb_email")
        logging.info("fb_email=%r", fb_email)
        if fb_email:
            self.user = UserProfile.query(UserProfile.email == fb_email).get()
            logging.info("auth token=%r", self.user.facebook_token)
            self.gconn = None
            self.fbconn = FBConnector(self.user.facebook_token)
            logging.info("now invoking %r", method)
            return method(self, *args)
        
        logging.info("redirecting to facebook")
        self.session["fb_email"] = None
        self.session["fb_redirect"] = self.request.url
        self.session["fb_state"] = generate_random_token(20)
        return self.redirect("https://www.facebook.com/dialog/oauth?"
            "client_id=%s&redirect_uri=%s&state=%s&scope=%s&response_type=code" % (
                settings.FB_CLIENT_ID, FB_URI, self.session["fb_state"], FB_SCOPES))
    return method2


class FBOauthHandler(BaseHandler):
    URL = "/fboauth"
    
    def get(self):
        if self.session["fb_state"] != self.request.GET["state"]:
            self.redirect_with_flashmsg("/", "Facebook login forged", "error")
        del self.session["fb_state"]
        code = self.request.params["code"]
        req = urllib2.urlopen("https://graph.facebook.com/oauth/access_token?"
            "client_id=%s&redirect_uri=%s&client_secret=%s&code=%s" % (
                settings.FB_CLIENT_ID, FB_URI, settings.FB_CLIENT_SECRET, code))
        reply = urlparse.parse_qs(req.read())
        logging.info("access token: %r", reply)
        if "access_token" not in reply:
            return self.redirect_with_flashmsg("/", "Login failed: %s" % (reply.get("error_description"),), "error")
        
        access_token = reply["access_token"][0]
        req = urllib2.urlopen("https://graph.facebook.com/me?access_token=%s" % (access_token,))
        data = req.read()
        logging.info("userinfo = %r", data)
        userinfo = json.loads(data)
        
        user = UserProfile.query(UserProfile.email == userinfo["email"]).get()
        if not user:
            user = UserProfile.query(UserProfile.facebook_id == userinfo["id"]).get()
        if not user:
            user = UserProfile(email = userinfo["email"], fullname = userinfo["name"])
        user.facebook_id = userinfo["id"]
        user.facebook_token = access_token
        user.put()
        self.session["fb_email"] = user.email
        
        url = str(self.session.pop("fb_redirect"))
        logging.info("fb auth successful, redirecting to %r", url)
        return self.redirect(url)


class FBLoginHandler(BaseHandler):
    URL = "/fblogin"
    
    @fb_logged_in
    def get(self, url):
        return self.redirect(url)


class FBConnector(object):
    def __init__(self, access_token):
        self.access_token = access_token
        self.myemail = None
        try:
            req = urllib2.urlopen("https://graph.facebook.com/me?access_token=%s" % (self.access_token,))
            ans = json.loads(req.read())
            self.myemail = ans["email"]
        except Exception:
            logging.error("FBConnector couldn't get my email")
    
    def get_friends(self, pattern, limit = 10):
        url = ("https://graph.facebook.com/fql?q=select+uid%2C+name+from+user+where+uid+in+"
            "(SELECT+uid2+FROM+friend+WHERE+uid1+%3D+me())+and+strpos(lower(name)%2C'$NAME')%3E%3D0+limit+$LIMIT&format=json&"
            "&access_token=$TOKEN")
        req = urllib2.urlopen(url.replace("$NAME", pattern.lower()).replace("$LIMIT", str(limit)).replace("$TOKEN", self.access_token)) 
         
        return [{"name":item["name"], "id":"%s/%s" % (item["uid"], item["name"])} for item in json.loads(req.read())["data"]]

    def send_message(self, userid, title, body, start_win, end_win):
        start = {'dateTime': start_win.isoformat() + "+02:00",}
        end = {'dateTime': end_win.isoformat() + "+02:00",}
        guest = [{'email': str(userid)}]
        event_info = {"summary":title, "start":start, "end":end, "description":body, "location":"", "attendees":guest}
        req = self.create_event(event_info)
        return req
    
    def create_event(self, event_info):
        logging.info(event_info["end"])
        logging.info(event_info["end"]["dateTime"])
        
        if event_info["end"]["dateTime"] == event_info["start"]["dateTime"]:
            data = urllib.urlencode(dict(
                                         name = event_info["summary"],
                                         start_time = event_info["start"]["dateTime"],
                                         description = event_info["description"],
                                         location = event_info["location"],
                                         privacy_type = "SECRET",
                                         ))
        else:
            data = urllib.urlencode(dict(
                                         name = event_info["summary"],
                                         start_time = event_info["start"]["dateTime"],
                                         end_time = event_info["end"]["dateTime"],
                                         description = event_info["description"],
                                         location = event_info["location"],
                                         privacy_type = "SECRET",
                                         ))
        req = urllib2.urlopen("https://graph.facebook.com/me/events?access_token=%s" % (self.access_token,), data)
        raw = req.read()
        ans = json.loads(raw)
        if "id" not in ans:
            logging.error("Error response from FB: %r", raw)
            raise ValueError("Failed to create FB event")
        event_id = ans["id"]

        #logging.info("guest: %r, guest id: %r", event_info["attendees"], event_info["attendees"]["email"])
        
        for att in event_info["attendees"]:
            logging.info("ATT[EMAIL]: %r",att["email"])
        
        req = urllib2.urlopen("https://graph.facebook.com/%s/invited?access_token=%s&users=%s" % (
            event_id, self.access_token, ",".join(att["email"] for att in event_info["attendees"])), " ")
        req.read()

        return event_id
        
    def get_events(self, start_date, end_date):
        q = ("SELECT eid, start_time, end_time, name FROM event " 
            "WHERE eid IN (SELECT eid FROM event_member WHERE uid = me() AND rsvp_status = 'attending') "
            "AND start_time >= '%s-%s-%s' AND end_time <= '%s-%s-%s'" % (start_date.year, start_date.month, start_date.day,
                end_date.year, end_date.month, end_date.day))
        url = "https://graph.facebook.com/fql?%s" % (urllib.urlencode({"q":q, "access_token":self.access_token}))
        req = urllib2.urlopen(url)
        ans = json.loads(req.read())
        events = []
        for evt in ans["data"]:
            e = {"summary" : evt["name"], "start" : {}, "end" : {}}
            if "T" in evt["start_time"]:
                e["start"]["dateTime"] = evt["start_time"]
            else:
                e["start"]["date"] = evt["start_time"]
            if evt["end_time"]:
                if "T" in evt["end_time"]:
                    e["end"]["dateTime"] = evt["end_time"]
                else:
                    e["end"]["date"] = evt["end_time"]
            else:
                if "T" in evt["start_time"]:
                    e["end"]["dateTime"] = (parse_datetime(evt["start_time"]) + timedelta(hours = 2)).isoformat()
                else:
                    e["end"]["date"] = evt["start_time"]
            
            events.append(e)
        return events
        

    
    def update_event(self, event_id, event_info):
        data = urllib.urlencode(dict(
            name = event_info["summary"],
            start_time = event_info["start"]["dateTime"],
            end_time = event_info["end"]["dateTime"],
            description = event_info["description"],
            location = event_info["location"],
        ))
        req = urllib2.urlopen("https://graph.facebook.com/%s?access_token=%s" % (event_id, self.access_token), data)
        req.read()

        req = urllib2.urlopen("https://graph.facebook.com/%s/invited?access_token=%s&users=%s" % (event_id, self.access_token))
        ans = json.loads(req.read())
        old_invited = set(user["id"] for user in ans["data"])
        new_invited = set(att["email"] for att in event_info["attendees"])
        to_remove = old_invited - new_invited
        to_add = new_invited - old_invited
        for uid in to_remove:
            del_url("https://graph.facebook.com/%s/invited/%s?access_token=%s" % (event_id, uid, self.access_token))
        
        if to_add:
            req = urllib2.urlopen("https://graph.facebook.com/%s/invited?access_token=%s&users=%s" % (
                event_id, self.access_token, ",".join(to_add)), " ")
            req.read()
    
    def cancel_event(self, event_id):
        resp = del_url('https://graph.facebook.com/%s?access_token=%s' % (event_id, self.access_token))
        #logging.info("DELETE: %r", resp.read())


def del_url(url):
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request(url)
    request.get_method = lambda: 'DELETE'
    resp = opener.open(request)
    return resp.read()




