from google.appengine.ext import ndb


class UserProfile(ndb.Model):
    email = ndb.StringProperty(required=True)


