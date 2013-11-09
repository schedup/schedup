import os
import webapp2
import jinja2
from webapp2_extras import sessions


_configured_urls = set()
with open(os.path.join(os.path.dirname(__file__), "../secret.key"), "rb") as f:
    secret_key = f.read().decode("base64")

app = webapp2.WSGIApplication([], 
    debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'),
    config = {
        'webapp2_extras.sessions' : {
            'secret_key': secret_key,
        }
    }
)


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




