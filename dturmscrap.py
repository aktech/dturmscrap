# DTU Resume Manager Scrapper

import sys
sys.path.insert(0, 'libs')   # Add libraries in the lib folder

import webapp2
from google.appengine.api import mail

import pickle
import logging
import cookielib
import urllib2
import mechanize
from bs4 import BeautifulSoup


# Globals
roll_no = 'YOUR_ROLL_NUMBER, e.g: 2K12/BR/001'
password = 'PASSWORD'
rm_url = 'http://tnp.dtu.ac.in/rm3y/login.php'
announce_style = ['color:#000000; font-family:Arial, Helvetica, sans-serif; '
                  'margin-left:20px; overflow:auto; content:inherit; '
                  'padding:10px;']

# Email Details
sender_address = 'admin@dturm-1021.appspotmail.com'  # application handle: 'dturm-1021'
user_address = ['YOUR_EMAIL_ADDRESS']
subject = 'DTU RM Notification'


from google.appengine.ext import db


class ObjectProperty(db.BlobProperty):
    # Use this property to store objects.
    def validate(self, value):
        try:
            result = pickle.dumps(value)
            return value
        except pickle.PicklingError, e:
            return super(ObjectProperty, self).validate(value)

    def get_value_for_datastore(self, model_instance):
        result = super(ObjectProperty, self).get_value_for_datastore(model_instance)
        result = pickle.dumps(result)
        return db.Blob(result)

    def make_value_from_datastore(self, value):
        try:
            value = pickle.loads(str(value))
        except:
            pass
        return super(ObjectProperty, self).make_value_from_datastore(value)


class MyEntity(db.Model):
    name = db.StringProperty()
    obj = ObjectProperty()


def open_browser(url):
    # Browser
    br = mechanize.Browser()
    # Enable cookie support for urllib2
    cookiejar = cookielib.LWPCookieJar()
    br.set_cookiejar(cookiejar)
    # Browser options
    br.set_handle_equiv(True)
    # br.set_handle_gzip(True)  # Experimental feature
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    # Headers
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1' ) ]
    # authenticate
    br.open(url)
    return br


def select_form(form):
    return form.attrs.get('action', None) == 'login.php'


def login(br, roll_no, password):
    # Username & Password
    br["stud_username"] = roll_no
    br["stud_password"] = password
    br.submit()


def get_news(br, announce_style):
    soup = BeautifulSoup(br.response().read(), "lxml")
    # TODO: Chose a better selection Method
    announce_news_soup = soup.findAll('h4', {'style': announce_style[0]})

    if not announce_news_soup:
        return ['Invalid announce_style']

    def slice_news(s):
        return s[133:-5]

    def add_news_id(a):
        for k, v in enumerate(a):
            hsh = '#'
            a[k] = ('UPDATE: {}{} \n' + a[k]).format(hsh, k+1)
        return a
    announce_news_str = map(str, announce_news_soup)
    all_news = map(slice_news, announce_news_str)
    all_news = add_news_id(all_news)
    return all_news


def latest_news(all_news):
    entities = MyEntity.all()
    entities = entities.fetch(1)
    if entities:
        old_news = entities[0].obj
    else:
        old_news = []
        logging.info("Old News Empty")
    latestnews = [item for item in all_news if item not in old_news]
    logging.info('old_news: %s', old_news)
    logging.info('latestnews: %s', latestnews)
    return latestnews


def save_news(all_news):
    entity = MyEntity(name="all_news", obj=all_news)
    entity.put()


class MainPage(webapp2.RequestHandler):
    def get(self):
        run_rmscrap()
        self.response.write("\n Success!\n")


def run_rmscrap():
    br = open_browser(rm_url)
    br.select_form(predicate=select_form)
    login(br, roll_no, password)

    # GET News
    allnews = get_news(br, announce_style)
    latestnews = latest_news(allnews)
    save_news(allnews)

    # SEND Latest News
    body = '\n'.join(latestnews)
    if body:
        mail.send_mail(sender_address, user_address, subject, body)
        logging.info("Mail Sent!")


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
