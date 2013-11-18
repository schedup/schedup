import os
import webapp2
import jinja2
from webapp2_extras import sessions
from oauth2client.appengine import OAuth2Decorator
from schedup import settings
from schedup.settings import SESSION_SECRET
import functools


app = webapp2.WSGIApplication([], 
    debug = True, #os.environ['SERVER_SOFTWARE'].startswith('Dev'),
    config = {
        'webapp2_extras.sessions' : {
            'secret_key': SESSION_SECRET,
        }
    }
)

oauth = OAuth2Decorator(client_id=settings.CLIENT_ID, client_secret=settings.CLIENT_SECRET,
    scope=settings.SCOPE)
app.router.add((oauth.callback_path, oauth.callback_handler()))

_configured_urls = set()

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
                    raise ValueError("URL %r already appears in routes" % (url,))
                app.router.add((url, cls2))
                _configured_urls.add(url)
            return cls2
    
    def render_response(self, _template, **params):
        temp = self.JINJA.get_template(_template)
        output = temp.render(params)
        self.response.write(output)

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


