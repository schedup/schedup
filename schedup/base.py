import webapp2

config = {
    "webapp2_extras.jinja2" : {
        "template_path" : "templates",
        "extensions" : [
            "jinja2.ext.loopcontrols",
        ],
    },
}

app = webapp2.WSGIApplication([], debug=True, config = config)

_configured_urls = set()

def _route(url):
    def deco(cls):
        if url in _configured_urls:
            raise ValueError("URL %r already appears in routes" % (url,))
        app.router.add((url, cls))
        _configured_urls.add(url)
        cls.URL = url
        return cls
    return deco

app.route = _route




