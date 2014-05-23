import numerous_apikey
import os
import sys
import time
import urllib2
import withings_auth
from withings import WithingsAccount

POUNDS_IN_KILOGRAMS = 2.20462262

def post_numerous_metric(metric_id, value):
  auth_handler = urllib2.HTTPBasicAuthHandler()

  url = "https://api.numerousapp.com/v1/metrics/%s/events" % metric_id


  auth_handler.add_password(realm = 'Numerous', uri = url, user = numerous_apikey.apikey, passwd='')
  opener = urllib2.build_opener(auth_handler)
  # ...and install it globally so it can be used with urlopen.
  urllib2.install_opener(opener)

  values = """ { "value": %s, "onlyIfChanged": true } """ % value
  headers = { 'Content-Type': 'application/json' }
  request = urllib2.Request(url, data=values, headers=headers)

  try:
    response_body = urllib2.urlopen(request).read()
    sys.stderr.write(response_body)
  except urllib2.URLError as e:
    sys.stderr.write("Error updating value to %s via url: %s: %s\n" % (value, url, e))


def get_withings_weight(fromdate, todate):


  # Withings API
  withings = WithingsAccount(withings_auth.username, withings_auth.password)
  user = withings.get_user_by_shortname(withings_auth.shortname)
  if not user:
      print 'could not find user: %s' % withings_auth.shortname
      return
  if not user.ispublic:
      print 'user %s has not opened withings data' % withings_auth.shortname
      return
  startdate = int(time.mktime(fromdate.timetuple()))
  enddate = int(time.mktime(todate.timetuple())) + 86399
  groups = user.get_measure_groups(startdate=startdate, enddate=enddate)

  weights = []
  for group in groups:
    dt = group.get_datetime()
    weight = group.get_weight()
    fat_ratio = group.get_fat_ratio()
    # print "date: %s " % dt
    # print "weight: %f lb" % (weight * POUNDS_IN_KILOGRAMS);
    # print "fat ratio: %f " % (fat_ratio or 0);
    weights.append(weight * POUNDS_IN_KILOGRAMS)
  return weights


