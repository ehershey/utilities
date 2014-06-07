import json
import os
import sys
import time
import urllib2
import withings_auth
from withings import WithingsAccount

POUNDS_IN_KILOGRAMS = 2.20462262
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


