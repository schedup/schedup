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
from schedup.settings import SESSION_SECRET
import inspect
import logging


app = webapp2.WSGIApplication([], 
    debug = True, #os.environ['SERVER_SOFTWARE'].startswith('Dev'),
    config = {
        'webapp2_extras.sessions' : {
            'secret_key': SESSION_SECRET,
        }
    }
)

oauth = OAuth2Decorator(
    client_id = settings.CLIENT_ID, 
    client_secret = settings.CLIENT_SECRET,
    scope = settings.OAUTH_SCOPES)
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
    
    def redirect_with_flashmsg(self, url, msg):
        self.session["flashmsg"] = msg
        logging.info("setting flashmsg to %r, redirect to %r", msg, url)
        return self.redirect(url)
    
    def render_response(self, _template, **params):
        if "flashmsg" not in params:
            msg = self.session.pop("flashmsg", None)
            params["flashmsg"] = msg
            logging.info("rendering flashmsg=%r", msg)
        if "user" not in params:
            params["user"] = getattr(self, "user", None)
        if "pageid" not in params:
            params["pageid"] = self.__class__.__name__
        params["logging"] = logging
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
        from schedup.models import UserProfile
        self.gconn = GoogleConnector(oauth)
        self.user = UserProfile.query(UserProfile.email == self.gconn.user_email).get()
        if not self.user:
            prof = self.gconn.get_profile()
            self.user = UserProfile(email = self.gconn.user_email, fullname = prof["name"])
            self.user.put()
        return method(self, *args)
    return method2

def maybe_logged_in(method):
    @oauth.oauth_aware
    @functools.wraps(method)
    def method2(self, *args):
        from schedup.connector import GoogleConnector
        from schedup.models import UserProfile
        if oauth.has_credentials():
            self.gconn = GoogleConnector(oauth)
            self.user = UserProfile.query(UserProfile.email == self.gconn.user_email).get()
            if not self.user:
                prof = self.gconn.get_profile()
                self.user = UserProfile(email = self.gconn.user_email, fullname = prof["name"])
                self.user.put()
        else:
            self.gconn = None
            self.user = None
        return method(self, *args)
    return method2


def api_call(**signature):
    def deco(method):
        argnames, _, _, defaults = inspect.getargspec(method)
        optional_argsnames = frozenset(argnames[-len(defaults):] if defaults else ())
        
        @functools.wraps(method)
        def method2(self):
            try:
                kwargs = {}
                for name, tp in signature.items():
                    if name not in self.request.params:
                        if name not in optional_argsnames:
                            raise KeyError("Missing parameter: %s" % (name,))
                    else:
                        kwargs[name] = tp(self.request.params[name])
                
                res = method(self, **kwargs)
            except Exception as ex:
                result = {"status" : "error", "exception" : repr(ex)}
                if app.debug:
                    result["traceback"] = "".join(traceback.format_exception(*sys.exc_info())).splitlines()
                self.response.status = 500
            else:
                result = {"status" : "ok", "value" : res}
                self.response.status = 200
            
            json_data = json.dumps(result)
            self.response.content_type = 'application/json'
            self.response.write(json_data)
        return method2
    return deco










