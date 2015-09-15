#!/usr/bin/python2.7
#
# mapmyfitness.py
#
# handle oauth for mapmyfitness and call authenticated api url's such as:
#
# http://api.mapmyfitness.com/3.1/users/get_user
# http://api.mapmyfitness.com/3.1/workouts/get_workouts
#
# usage: mapmyfitness.py <url>
#
# Script will try to open a web browser for authentication, storing oauth
# tokens for re-use once retrieved in $HOME/.mapmyfitness_tokens.json
#
# Requires mapmyfitness_apikeys.py file in path with api keys in the form:
#
# consumer_key = u"xxx"
# secret_key = u"xxx"
#

from __future__ import unicode_literals

import argparse
import io
import json
import urlparse
import os
import sys
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import requests
from requests_oauthlib import OAuth1
from oauthlib.oauth1.rfc5849.utils import escape
from oauth2client.file import Storage
import webbrowser

import mapmyfitness_apikeys


parser = argparse.ArgumentParser()
parser.add_argument("url", help="URL to access")
args = parser.parse_args()

tokenfilename = os.getenv("HOME") + "/.mapmyfitness_tokens.json"
token_credentials = None

if os.path.exists(tokenfilename):
    tokenfile = open(tokenfilename, "r")
    token_credentials = json.load(tokenfile)
    tokenfile.close()

client_key = mapmyfitness_apikeys.consumer_key
client_secret = mapmyfitness_apikeys.secret_key


if token_credentials is None or len(token_credentials) != 2:

    temporary_credentials_url = 'http://api.mapmyfitness.com/3.1/oauth/request_token'

    callback_uri = 'http://' + os.uname()[1] + ':12345/'

    oauth = OAuth1(client_key, client_secret=client_secret,
                   callback_uri=callback_uri, signature_type='BODY')

    r = requests.post(url=temporary_credentials_url,
                      headers={'Content-Type': 'application/x-www-form-urlencoded',
                               'Accept': 'application/x-www-form-urlencoded'},
                      auth=oauth)

    print(r.request.body)

    temporary_credentials = urlparse.parse_qs(r.content)

    authorize_url = 'https://www.mapmyfitness.com/oauth/authorize/?oauth_token=%s&oauth_callback=%s' % (
        temporary_credentials['oauth_token'][0], escape(callback_uri))

    print "sending to url"
    print "authorize_url: %s" % authorize_url

    if os.fork() == 0:
        webbrowser.open(authorize_url)
        exit()

    class AuthorizationHandler(BaseHTTPRequestHandler):

        def do_GET(self):
            self.send_response(200, 'OK')
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write("Authorization received")
            self.server.path = self.path

    server_address = (urlparse.urlparse(callback_uri).hostname,
                      urlparse.urlparse(callback_uri).port)
    print "server_address: "
    print server_address
    httpd = HTTPServer(server_address, AuthorizationHandler)
    httpd.handle_request()

    verifier_url = urlparse.urlparse(httpd.path)
    verifier_query = urlparse.parse_qs(verifier_url.query)
    oauth = OAuth1(client_key, client_secret,
                   unicode(temporary_credentials['oauth_token'][0]),
                   unicode(temporary_credentials['oauth_token_secret'][0]),
                   callback_uri=callback_uri,
                   signature_type='BODY',
                   verifier=verifier_query['oauth_verifier'][0])
    token_credentials_url = 'http://api.mapmyfitness.com/3.1/oauth/access_token'

    r = requests.post(url=token_credentials_url,
                      headers={'Content-Type':
                               'application/x-www-form-urlencoded',
                               'Accept': 'application/x-www-form-urlencoded'},
                      auth=oauth)

    token_credentials = urlparse.parse_qs(r.content)

    try:
        tokenfile = open(tokenfilename, "w")
        json.dump(token_credentials, tokenfile)
        tokenfile.close()
    except:
        os.unlink(tokenfilename)
        print("Error saving credentials")
        print "Unexpected error:", sys.exc_info()[0]
        raise


oauth = OAuth1(client_key, client_secret, unicode(token_credentials['oauth_token'][
               0]), unicode(token_credentials['oauth_token_secret'][0]), signature_type='QUERY')

r = requests.get(url=args.url, auth=oauth)

print(r.content)
