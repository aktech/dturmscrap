# DTU RM Scrapper
# Author: AMiT Kumar <dtu.amit@gmail.com>
# Version: 0.1

import sys
sys.path.insert(0, 'libs')

import webapp2
from google.appengine.api import mail
from google.appengine.ext import db

import pickle
import logging
import cookielib
import urllib2
import mechanize
from bs4 import BeautifulSoup


# Globals
roll_no = 'ROLL_NO'
password = 'PASSWORD'
rm_url = 'http://tnp.dtu.ac.in/rm3y/login.php'

# Email Details
sender_address = 'admin@dturm-1021.appspotmail.com'  # This is based on your GAE ID
user_address = ['USER-EMAIL']

subject = 'DTU RM Notification'


# HTML Parser
from HTMLParser import HTMLParser


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


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
    obj = ObjectProperty()  # Kudos


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


def get_news(br, announce_style=None):
    soup = BeautifulSoup(br.response().read())
    # announce_news_soup = soup.findAll('h4', {'style': announce_style[0]})
    announce_news_soup = soup.find_all('h4', attrs = {'style' : True, 'align': False})
    if not announce_news_soup:
        return ['Invalid scrap']
    def get_contents(s):
        return s.contents
    announce_news_content = map(get_contents, announce_news_soup)
    all_news = map(str, announce_news_content)
    all_news = map(strip_tags, all_news)
    all_news = all_news[:25:]
    return all_news


def add_news_id(a):
    for k, v in enumerate(a):
        hsh = '#'
        a[k] = ('UPDATE: {}{} \n' + a[k]).format(hsh, k+1)
    return a


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
    latestnews = add_news_id(latestnews)
    logging.info('latestnews: %s', latestnews)
    return latestnews


def save_news(all_news):
    db.delete(MyEntity.all(keys_only=True))
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
    allnews = get_news(br)
    latestnews = latest_news(allnews)
    if latestnews:
        save_news(allnews)
        logging.info('Saved News: %s', allnews)

    # SEND Latest News
    body = '\n'.join(latestnews)
    if body:
        mail.send_mail(sender_address, user_address, subject, body)
        logging.info("Mail Sent!")
    else:
        logging.info("No Latest News Found")


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
