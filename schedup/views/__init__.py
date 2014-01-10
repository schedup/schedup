from schedup.base import BaseHandler, maybe_logged_in, logged_in
import schedup.views.apis
import schedup.views.event_list
import schedup.views.new_event
import schedup.views.profile
import schedup.views.calendar


class MainPage(BaseHandler):
    URL = "/"
    @maybe_logged_in
    def get(self):
        if self.user:
            self.redirect("/my")
        else:
            self.render_response('landing.html', hide_header = True)


class HelpPage(BaseHandler):
    URL = "/help"
    def get(self):
        self.render_response('landing.html')


class SignUpRedirect(BaseHandler):
    URL = "/signup"
    
    @logged_in
    def get(self):
        return self.redirect(self.request.get("redirect"))


class AboutPage(BaseHandler):
    URL = "/about"
    
    def get(self):
        self.render_response("about.html", section="about")




