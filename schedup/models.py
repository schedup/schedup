from google.appengine.ext import ndb


class MyModel(ndb.Model):
    email = ndb.StringProperty(required=True)
    platform = ndb.StringProperty(required=False)


