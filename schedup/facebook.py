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

class FBLoginHandler(BaseHandler):
    URL = "/fblogin"
    
    def get(self):
        pass

def fb_logged_in(method):
    @functools.wraps(method)
    def method2(self, *args):
        if self.session.get("fb_token"):
            return method(*args)
        
        self.session["fb_token"] = None
        self.session["fb_redirect"] = self.request.url
        self.session["fb_state"] = generate_random_token(20)
        return self.redirect("https://www.facebook.com/dialog/oauth?"
            "client_id=%s&redirect_uri=%s&state=%s&scope=%s&response_type=code" % (
                settings.FB_CLIENT_ID, FB_URI, self.session["fb_state"], FB_SCOPES))


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
        self.session["fb_token"] = access_token
        req = urllib2.urlopen("https://graph.facebook.com/me?access_token=%s" % (access_token,))
        data = req.read()
        logging.info("userinfo = %r", data)
        userinfo = json.loads(data)
        
        self.user = UserProfile.query(UserProfile.email == userinfo["email"]).get()
        if not self.user:
            self.user = UserProfile(email = userinfo["email"], fullname = userinfo["name"], 
                facebook_token = access_token)
            self.user.put()
        
        return self.redirect(self.session.pop("fb_redirect"))

class FBConnector(object):
    "https://graph.facebook.com/me/friends"








