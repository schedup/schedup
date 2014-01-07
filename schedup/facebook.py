import functools
from schedup.base import BaseHandler, ON_DEV
from schedup import settings
import logging
import urllib2
import urlparse
import json
from schedup.models import UserProfile
from schedup.utils import generate_random_token


FB_SCOPES = "email,create_event,rsvp_event,user_events,manage_notifications"

if ON_DEV:
    FB_URI = "http://localhost:8080/fboauth"
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
            user = UserProfile(email = userinfo["email"], fullname = userinfo["name"])
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
    
    def get_friends(self, pattern, limit = 10):
        req = urllib2.urlopen("https://graph.facebook.com/fql?q=select+uid%2C+name+from+user+where+uid+in+"
            "(SELECT+uid2+FROM+friend+WHERE+uid1+%3D+me())+and+strpos(lower(name)%2C'$NAME')%3E%3D0+limit+$LIMIT&format=json&"
            "suppress_http_code=1&access_token=$TOKEN".replace("$NAME", pattern.lower()).
                                                       replace("$LIMIT", str(limit)).
                                                       replace("$TOKEN", self.access_token))    
        return [{"name":item["name"], "id":str(item["uid"])} for item in json.loads(req.read())["data"]]

    def send_message(self, userid, text):
        pass
    
    def notify(self, text, url):
        pass
    
    def create_event(self, info):
        pass
    
    def get_events(self, start_date, end_date):
        pass
    
    def update_event(self, eventid, info):
        pass
    
    def cancel_event(self, eventid):
        pass








