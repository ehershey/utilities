#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Simple command-line example for Calendar.

Command-line application that lists a user's calendars

Usage:
  $ python listcalendars.py

You can also get help on all the command-line flags the program understands
by running:

  $ python listcalendars.py --help

To get detailed log output run:

  $ python listcalendars.py --logging_level=DEBUG
"""

__author__ = 'ernie.hershey@10gen.com'


import argparse
import datetime
import httplib2
import logging
import os
import pprint
import simplejson as json
import sys
import urllib

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run



# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>
CLIENT_SECRETS = 'client_secrets.json'

# Helpful message to display in the browser if the CLIENT_SECRETS file
# is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console <https://code.google.com/apis/console>.

""" % os.path.join(os.path.dirname(__file__), CLIENT_SECRETS)

# Set up a Flow object to be used if we need to authenticate.
FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/calendar.readonly',
    message=MISSING_CLIENT_SECRETS_MESSAGE)


parser = argparse.ArgumentParser(description='List calendars')
# parser.add_argument('--min-time', type=int, required=True, help='Minimum timestamp for history in seconds since the epoch')
# parser.add_argument('--max-time', type=int, required=True, help='Maximum timestamp for history in seconds since the epoch')
# parser.add_argument('--max-results', type=int, required=False, help='Maximum number of results to return', default=100)
# parser.add_argument('--include-delta', action='store_true', required=False, help='Whether to include distance and speed relative to previous point', default=True)
# parser.add_argument('--verbose-timestamps', action='store_true', help='Whether to include an extra column with human readable timestamps')
args = parser.parse_args()


def main(argv):

  # Set the log level
  logging.getLogger().setLevel(getattr(logging, "DEBUG"))

  # If the Credentials don't exist or are invalid run through the native client
  # flow. The Storage object will ensure that if successful the good
  # Credentials will get written back to a file.
  storage = Storage('calendars.dat')
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run(FLOW, storage)

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with our good Credentials.
  http = httplib2.Http()
  http = credentials.authorize(http)

  try:

    resp, content = http.request("https://www.googleapis.com/calendar/v3/users/me/calendarList", "GET")
    if resp['status'] != '200':
        raise Exception("Invalid response %s. (Content follows)\n%s" % (resp['status'], content))
    json_list = json.loads(content)

    print(json_list)

  except AccessTokenRefreshError:
    print ("The credentials have been revoked or expired, please re-run"
      "the application to re-authorize")


if __name__ == '__main__':
  main(sys.argv)

