from google.appengine.ext import db
from google.appengine.api import users


class User(db.Model):
    _added      = db.DateTimeProperty(auto_now_add = True)
    _changed    = db.DateTimeProperty(auto_now = True)
    email       = db.StringProperty()
    is_allowed  = db.BooleanProperty(default=False)
    favourites  = db.ListProperty(db.Key)


def Authorize():
    user = users.get_current_user()
    if not user:
        return False
    u = db.Query(User).filter('email', user.email()).get()
    if not u:
        u = User()
        u.email = user.email()
        u.put()
    if u.is_allowed == False:
        return False
    return True

def CurrentUser():
    user = users.get_current_user()
    if user:
        return db.Query(User).filter('email', user.email()).get()


class Show(db.Model):
    title       = db.StringProperty()
    path        = db.StringProperty()
    find        = db.StringProperty()
    find_order  = db.IntegerProperty(default=9)


class Archive(db.Model):
    _added      = db.DateTimeProperty(auto_now_add = True)
    _changed    = db.DateTimeProperty(auto_now = True)
    channel     = db.StringProperty()
    group       = db.StringProperty()
    date        = db.DateTimeProperty()
    title       = db.StringProperty()
    episode     = db.StringProperty()
    url         = db.StringProperty()
    description = db.TextProperty()
    info_from   = db.StringProperty()
