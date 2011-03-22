import sys
import os.path

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.db import BadKeyError
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class Proxy(db.Model):
    name = db.StringProperty(required=True)
    url = db.LinkProperty(required=True)
    approved = db.BooleanProperty(default=False, required=True)

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        template_values = {
            'proxies': db.GqlQuery(
                'SELECT * FROM Proxy WHERE approved = true ORDER BY name'),
            'login_url': users.create_login_url('/'),
            'logout_url': users.create_logout_url('/'),
            'is_logged_in': user is not None,
            'is_admin': users.is_current_user_admin(),
        }

        if users.is_current_user_admin():
            template_values['moderated_proxies'] = db.GqlQuery(
                    'SELECT * FROM Proxy WHERE approved = false ORDER BY name')

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class AddProxy(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user is None:
            self.redirect('/')

        proxy = Proxy(
            name=self.request.get('name'),
            url=self.request.get('url'),
            approved=users.is_current_user_admin(),
        )
        proxy.put()

        template_values = {
            'is_admin': proxy.approved,
        }

        path = os.path.join(os.path.dirname(__file__), 'addproxy.html')
        self.response.out.write(template.render(path, template_values))

class EditProxy(webapp.RequestHandler):
    def post(self):
        if not users.is_current_user_admin():
            self.redirect('/')

        try:
            proxy = Proxy.get(self.request.get('id'))
        except BadKeyError:
            self.redirect('/')
            return

        action = self.request.get('action').lower()
        if action == 'add':
            proxy.approved = True
            proxy.put()
        elif action == 'delete':
            proxy.delete()
        elif action == 'remove':
            proxy.approved = False
            proxy.put()

        self.redirect('/')

def main():
    app = webapp.WSGIApplication([
            ('/', MainPage),
            ('/addproxy', AddProxy),
            ('/editproxy', EditProxy),
        ], debug=True)
    run_wsgi_app(app)

if __name__ == '__main__':
    main()