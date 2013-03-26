#!/usr/bin/python
from __future__ import unicode_literals

import urlparse
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import requests
from requests_oauthlib import OAuth1
from oauthlib.oauth1.rfc5849.utils import escape
from oauth2client.file import Storage
import webbrowser

import apikeys



client_key = apikeys.consumer_key
client_secret = apikeys.secret_key

storage = Storage('latitude.dat')
token_credentials = storage.get()

if credentials is None or credentials.invalid:

  temporary_credentials_url = 'http://api.mapmyfitness.com/3.1/oauth/request_token'

  callback_uri='http://127.0.0.1:12345/'

  oauth = OAuth1(client_key, client_secret=client_secret, callback_uri=callback_uri, signature_type='BODY')
  
  r = requests.post(url=temporary_credentials_url, 
      headers={'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/x-www-form-urlencoded'},
      auth=oauth)

  print(r.request.body)

  temporary_credentials = urlparse.parse_qs(r.content)

  authorize_url = 'https://www.mapmyfitness.com/oauth/authorize/?oauth_token=%s&oauth_callback=%s' % (temporary_credentials['oauth_token'][0], escape(callback_uri))
  
  webbrowser.open(authorize_url)
  
  class AuthorizationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
      self.send_response(200, 'OK')
      self.send_header('Content-Type', 'text/html')
      self.end_headers()
      self.server.path = self.path
  
  server_address = (urlparse.urlparse(callback_uri).hostname, urlparse.urlparse(callback_uri).port)
  httpd = HTTPServer(server_address, AuthorizationHandler)
  httpd.handle_request()
  
  verifier_url = urlparse.urlparse(httpd.path)
  verifier_query = urlparse.parse_qs(verifier_url.query)
  oauth = OAuth1(client_key, client_secret, 
      unicode(temporary_credentials['oauth_token'][0]), 
      unicode(temporary_credentials['oauth_token_secret'][0]), 
      callback_uri='http://127.0.0.1:12345/', 
      signature_type='BODY', 
      verifier=verifier_query['oauth_verifier'][0])
  token_credentials_url = 'http://api.mapmyfitness.com/3.1/oauth/access_token'

  r = requests.post(url=token_credentials_url, 
      headers={'Content-Type': 
        'application/x-www-form-urlencoded', 
        'Accept': 'application/x-www-form-urlencoded'}, 
      auth=oauth)

  token_credentials = urlparse.parse_qs(r.content)

resource_url = 'http://api.mapmyfitness.com/3.1/users/get_user'




oauth = OAuth1(client_key, client_secret, unicode(token_credentials['oauth_token'][0]), unicode(token_credentials['oauth_token_secret'][0]), signature_type='QUERY')

r = requests.get(url=resource_url, auth=oauth)

# user object:
#
print(r.content)

r = requests.get(url='http://api.mapmyfitness.com/3.1/workouts/get_workouts', auth=oauth)

# workouts:
#
print(r.content)
