from google.appengine.ext import db
from google.appengine.api import users


class User(db.Model):
    _added      = db.DateTimeProperty(auto_now_add = True)
    _changed    = db.DateTimeProperty(auto_now = True)
    email       = db.StringProperty()
    is_allowed  = db.BooleanProperty(default=False)


def Authorize(r):
    user = users.get_current_user()
    u = db.Query(User).filter('email', user.email()).get()
    if not u:
        u = User()
        u.email = user.email()
        u.put()

    if u.is_allowed == False:
        r.redirect(users.create_logout_url('/'))
        return False

    return True
