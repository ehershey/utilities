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

"""Simple command-line example for Latitude.

Command-line application that sets the users
current location.

Usage:
  $ python latitude.py

You can also get help on all the command-line flags the program understands
by running:

  $ python latitude.py --help

To get detailed log output run:

  $ python latitude.py --logging_level=DEBUG
"""

__author__ = 'jcgregorio@google.com (Joe Gregorio)'

EARTH_RADIUS_MILES = 3961

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
    scope='https://www.googleapis.com/auth/latitude.all.best',
    message=MISSING_CLIENT_SECRETS_MESSAGE)


parser = argparse.ArgumentParser(description='Look up latitude history')
parser.add_argument('--min-time', type=int, required=True, help='Minimum timestamp for history in seconds since the epoch')
parser.add_argument('--max-time', type=int, required=True, help='Maximum timestamp for history in seconds since the epoch')
parser.add_argument('--max-results', type=int, required=False, help='Maximum number of results to return', default=100)
parser.add_argument('--include-delta', action='store_true', required=False, help='Whether to include distance and speed relative to previous point', default=True)
parser.add_argument('--verbose-timestamps', action='store_true', help='Whether to include an extra column with human readable timestamps')
args = parser.parse_args()


def main(argv):

  # Set the log level
  logging.getLogger().setLevel(getattr(logging, "DEBUG"))

  # If the Credentials don't exist or are invalid run through the native client
  # flow. The Storage object will ensure that if successful the good
  # Credentials will get written back to a file.
  storage = Storage('latitude.dat')
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run(FLOW, storage)

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with our good Credentials.
  http = httplib2.Http()
  http = credentials.authorize(http)

  try:
    params = {
      'granularity': 'best',
      'max-results': args.max_results,
      'min-time': args.min_time * 1000,
      'max-time': args.max_time * 1000,
      'alt': 'json',
    }

    resp, content = http.request("https://www.googleapis.com/latitude/v1/location?" + urllib.urlencode(params), "GET")
    if resp['status'] != '200':
        raise Exception("Invalid response %s. (Content follows)\n%s" % (resp['status'], content))
    json_list = json.loads(content)


    if 'items' in json_list['data']:
      last_longitude = None
      last_latitude = None
      for loc in reversed(json_list['data']['items']):
        longitude = loc['longitude']
        latitude =  loc['latitude']
        del loc['longitude']
        del loc['latitude']
        loc['loc'] = [longitude, latitude];
        del loc['kind']
        loc['source'] = 'latitude'
        loc['timestamp'] = {"$date": loc['timestampMs']};
        del loc['timestampMs']

        if args.include_delta and last_longitude and last_latitude:
          loc['distance_traveled'] = distance_on_unit_sphere(latitude, longitude, last_latitude, last_longitude)
          loc['distance_traveled_units'] = 'mph'

        last_longitude = longitude
        last_latitude = latitude
        print loc

      #if(args.verbose_timestamps):
      #if(True):
        #print "latitude, longitude, timestamp, accuracy, verbose timestamp"
        #for loc in reversed(json_list['data']['items']):
          ##print loc
          #print "%s, %s, %s, %s, %s" % (loc['latitude'], loc['longitude'], loc['timestampMs'], loc.get('accuracy', -1), datetime.datetime.fromtimestamp(float(loc['timestampMs'])/1000))
      #else:
        #print "latitude, longitude, timestamp, accuracy"
        #for loc in reversed(json_list['data']['items']):
          #print "%s, %s, %s, %s" % (loc['latitude'], loc['longitude'], loc['timestampMs'], loc.get('accuracy', -1))



  except AccessTokenRefreshError:
    print ("The credentials have been revoked or expired, please re-run"
      "the application to re-authorize")

import math

def distance_on_unit_sphere(lat1, long1, lat2, long2):

    # Convert latitude and longitude to
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0

    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians

    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians

    # Compute spherical distance from spherical coordinates.

    # For two locations in spherical coordinates
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) =
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length

    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos(cos)

    # Remember to multiply arc by the radius of the earth
    # in your favorite set of units to get length.
    return arc * EARTH_RADIUS_MILES

if __name__ == '__main__':
  main(sys.argv)

