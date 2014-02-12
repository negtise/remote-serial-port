#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import cgi
import datetime
import logging
import webapp2
import copy

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import memcache


guestbook_key = ndb.Key('Guestbook', 'default_guestbook')

class Greeting(ndb.Model):
  author = ndb.UserProperty()
  content = ndb.TextProperty()
  date = ndb.DateTimeProperty(auto_now_add=True)


class MainPage(webapp2.RequestHandler):
  def get(self):
    self.response.out.write('<html><body>')

    greetings = ndb.gql('SELECT * '
                        'FROM Greeting '
                        'WHERE ANCESTOR IS :1 '
                        'ORDER BY date DESC LIMIT 10',
                        guestbook_key)

    for greeting in greetings:
      if greeting.author:
        self.response.out.write('<b>%s</b> wrote:' % greeting.author.nickname())
      else:
        self.response.out.write('An anonymous person wrote:')
      self.response.out.write('<blockquote>%s</blockquote>' %
                              cgi.escape(greeting.content))


    self.response.out.write("""
          <form action="/sign" method="post">
            <div><textarea name="content" rows="3" cols="60"></textarea></div>
            <div><input type="submit" value="Sign Guestbook"></div>
          </form>
        </body>
      </html>""")


class Guestbook(webapp2.RequestHandler):
  def post(self):
    greeting = Greeting(parent=guestbook_key)
    if users.get_current_user():
      greeting.author = users.get_current_user()
    greeting.content = self.request.get('content')
    greeting.put()
    self.redirect('/')

client = memcache.Client()
def SetDataCache(key,data):
    """
    client = memcache.Client()
    key = str(key)
    if not client.gets(key):
        return None
    while True: # Retry loop
        counter = client.gets(key)
        if client.cas(key, data):
            break
    """
    memcache.set(str(key),data)
    ret = memcache.get(str(key))
    logging.info('++++++++++++++++SetDataCache return %s'%(ret,))

def GetDataCache(key):
    """
    key = str(key)
#    client = memcache.Client()
    return client.gets(key)
    """
    return memcache.get(str(key))

def ClearDataCache(key):
    memcache.set(str(key),None)
    """
    key = str(key)
#    client = memcache.Client()
    if not client.gets(key):
        return
    while True: # Retry loop
        if client.cas(key, None):
            break
    """
SERVER_SLOT=0
SLOT_COUNT=30
CLIENT_SLOT=SERVER_SLOT+SLOT_COUNT

def ServerGetSlot():
    for i in xrange(SERVER_SLOT,SERVER_SLOT+SLOT_COUNT):
        if None == GetDataCache(i):
            return i
    return None

def ClientGetSlot():
    for i in xrange(CLIENT_SLOT,CLIENT_SLOT+SLOT_COUNT):
        if None == GetDataCache(i):
            return i
    return None

class ServerPost(webapp2.RequestHandler):
    def post(self):
        cmd = self.request.get('cmd')
        data = self.request.get('data')
        if cmd == 'clear':
            for i in xrange(SERVER_SLOT,SERVER_SLOT+SLOT_COUNT):
                ClearDataCache(i)
            logging.info('+++++++++++++PostService')
            self.response.out.write('OK')
            return

        counter = self.request.get('counter')
        counter = int(counter)
        
        slot = ServerGetSlot()

        if None==slot:
            self.response.out.write('full')
            return

#        logging.info('++++++++++++++++++++PostService %s'%(key1,))
        SetDataCache(slot,(counter,data))
        logging.info('+++++++++++++++++get slot %s'%(str(GetDataCache(slot)),))
        self.response.out.write('OK')

class ClientGet(webapp2.RequestHandler):
    def get(self):
        data = []
        for i in xrange(SERVER_SLOT,SERVER_SLOT+SLOT_COUNT):
            d = GetDataCache(i)
            if d:
                data.append(d)
                ClearDataCache(i)
                logging.info('+++++++++++++PostService')
        logging.info('++++++++++data:%s'%(str(data),))
        if not data:
            return
        data.sort()
        value = []
        for d in data:
            value.append(d[1])
        self.response.out.write(''.join(value))
        logging.info('++++++++++++++++++++ClientGet'+''.join(value))

class ServerGet(webapp2.RequestHandler):
    def get(self):
        data = []
        for i in xrange(CLIENT_SLOT,CLIENT_SLOT+SLOT_COUNT):
            d = GetDataCache(i)
            if d:
                data.append(d)
                ClearDataCache(i)
                logging.info('+++++++++++++PostService')
        logging.info('++++++++++data:%s'%(str(data),))
        if not data:
            return
        data.sort()
        value = []
        for d in data:
            value.append(d[1])
        self.response.out.write(''.join(value))
        logging.info('++++++++++++++++++++ServerGet'+''.join(value))

class ClientPost(webapp2.RequestHandler):
    def post(self):
        cmd = self.request.get('cmd')
        data = self.request.get('data')
        counter = self.request.get('counter')
        counter = int(counter)

        if cmd == 'clear':
            for i in xrange(CLIENT_SLOT,CLIENT_SLOT+SLOT_COUNT):
                ClearDataCache(i)
            logging.info('+++++++++++++PostService')
            self.response.out.write('OK')
            return

        slot = ClientGetSlot()
        if not slot:
            self.response.out.write('full')
            return
#        logging.info('++++++++++++++++++++PostService %s'%(key1,))
        SetDataCache(slot,(counter,data))
        logging.info('+++++++++++++++++get slot %s'%(str(GetDataCache(slot)),))
        self.response.out.write('OK')

app = webapp2.WSGIApplication([
  ('/client_post', ClientPost),
  ('/client_get', ClientGet),
  ('/server_post', ServerPost),
  ('/server_get', ServerGet),
  ('/', MainPage),
  ('/sign', Guestbook)
], debug=True)
