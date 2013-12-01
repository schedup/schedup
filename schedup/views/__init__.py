from schedup.base import BaseHandler, maybe_logged_in
import schedup.views.apis
import schedup.views.guest
import schedup.views.event_list
import schedup.views.new_event
import schedup.views.profile


class MainPage(BaseHandler):
    URL = "/"
    @maybe_logged_in
    def get(self):
        if self.user:
            self.redirect("/my")
        else:
            self.render_response('landing.html', hide_header = True)

class AboutPage(BaseHandler):
    URL = "/about"
    
    def get(self):
        self.render_response("about.html")




