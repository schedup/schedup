import os
import webapp2
import jinja2
import functools
import json
import sys
import traceback
from webapp2_extras import sessions
from oauth2client.appengine import OAuth2Decorator
from schedup import settings


ON_DEV = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication([],
    debug = True,
    config = {
        'webapp2_extras.sessions' : {
            'secret_key': settings.SESSION_SECRET,
        }
    }
)

oauth = OAuth2Decorator(
    client_id = settings.CLIENT_ID, 
    client_secret = settings.CLIENT_SECRET,
    scope = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/calendar',
        'https://www.google.com/m8/feeds',
    ],
)
app.router.add((oauth.callback_path, oauth.callback_handler()))

_configured_urls = {}

class BaseHandler(webapp2.RequestHandler):
    JINJA = jinja2.Environment(
        loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "../templates")),
        extensions = ['jinja2.ext.autoescape'],
        autoescape = True,
    )
    
    class __metaclass__(type):
        def __new__(cls, name, bases, namespace):
            cls2 = type.__new__(cls, name, bases, namespace)
            if namespace.get("URL"):
                url = namespace["URL"]
                if url in _configured_urls:
                    raise ValueError("URL %r already appears in routes: %r conflicts with %r" % 
                        (url, _configured_urls[url], cls2))
                app.router.add((url, cls2))
                _configured_urls[url] = cls2
            return cls2
    
    def redirect_with_flashmsg(self, url, msg, style="note"):
        self.session["flashmsg"] = msg
        self.session["flashclass"] = style
        return self.redirect(url)
    
    def redirect_with_context(self, url, **params):
        self.session.update(params)
        return self.redirect(url)
    
    def render_response(self, _template, **params):
        if not params.get("flashmsg"):
            params["flashmsg"] = self.session.pop("flashmsg", None)
        if "flashclass" not in params:
            params["flashclass"] = self.session.pop("flashclass", "note")
        if "flashtimeout" not in params:
            params["flashtimeout"] = self.session.pop("flashtimeout", 8) * 1000
        if not params.get("user"):
            params["user"] = getattr(self, "user", None)
        if "pageid" not in params:
            params["pageid"] = self.__class__.__name__
        temp = self.JINJA.get_template(_template)
        output = temp.render(params)
        self.response.write(output)
    
    def render_template(self, _template, **params):
        temp = self.JINJA.get_template(_template)
        return temp.render(params)
        
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()


def logged_in(method):
    @oauth.oauth_required
    @functools.wraps(method)
    def method2(self, *args):
        from schedup.connector import GoogleConnector
        from schedup.facebook import FBConnector
        from schedup.models import UserProfile
        self.gconn = GoogleConnector(oauth)
        self.user = UserProfile.query(UserProfile.email == self.gconn.user_email).get()
        if not self.user:
            prof = self.gconn.get_profile()
            self.user = UserProfile(email = self.gconn.user_email, fullname = prof["name"])
            self.user.put()
        if self.user.facebook_token:
            self.fbconn = FBConnector(self.user.facebook_token)
        else:
            self.fbconn = None
        return method(self, *args)
    return method2

def maybe_logged_in(method):
    @functools.wraps(method)
    def method2(self, *args):
        from schedup.connector import GoogleConnector
        from schedup.models import UserProfile
        from schedup.facebook import FBConnector
        
        # only start the dance if we have the cookies
        if "ACSID" in self.request.cookies or "dev_appserver_login" in self.request.cookies:
            @oauth.oauth_aware
            def aware(self, *args):
                if oauth.has_credentials():
                    self.gconn = GoogleConnector(oauth)
                    self.user = UserProfile.query(UserProfile.email == self.gconn.user_email).get()
                    if not self.user:
                        prof = self.gconn.get_profile()
                        self.user = UserProfile(email = self.gconn.user_email, fullname = prof["name"])
                        self.user.put()
                    if self.user.facebook_token:
                        self.fbconn = FBConnector(self.user.facebook_token)
                    else:  
                        self.fbconn = None
                else:
                    self.gconn = None
                    self.fbconn = None
                    self.user = None
                return method(self, *args)
            return aware(self, *args)
        
        elif "fb_email" in self.session:
            self.user = UserProfile.query(UserProfile.email == self.session["fb_email"]).get()
            self.gconn = None
            self.fbconn = FBConnector(self.user.facebook_token)
            return method(self, *args)
        
        else:
            self.gconn = None
            self.fbconn = None
            self.user = None
            return method(self, *args)
    return method2


def json_handler(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            res = method(self, *args, **kwargs)
        except Exception as ex:
            res = {"status" : "error", "exception" : repr(ex)}
            if app.debug:
                res["traceback"] = "".join(traceback.format_exception(*sys.exc_info())).splitlines()
            self.response.status = 500
        else:
            self.response.status = 200
        
        json_data = json.dumps(res)
        self.response.content_type = 'application/json'
        self.response.write(json_data)
    return wrapper








