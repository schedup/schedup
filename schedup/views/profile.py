from schedup.base import BaseHandler, logged_in


class ProfilePage(BaseHandler):
    URL = "/profile"
    
    @logged_in
    def get(self):
        self.render_response('profile.html', section="profile")



