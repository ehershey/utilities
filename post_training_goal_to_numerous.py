#!/usr/bin/env python
# vim: set filetype=python expandtab tabstop=2 softtabstop=2 shiftwidth=2 autoindent smartindent:
#
# Post training goal for the day to Numerous
#

import datetime
from numerousapp import update_metric_value
from pymongo import MongoClient, DESCENDING


DB = "ernie_org"
TRAINING_SCHEDULES_COLLECTION = "training_schedule"
ACTIVITY_TYPE='Running'

METRIC_ID = 5818738672989877729


def main():

  today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
  twelve_hours_ago = today - datetime.timedelta(hours=12)
  twelve_hours_from_now = today + datetime.timedelta(hours=12)

  client = MongoClient('localhost', 27017)
  db = client[DB]

  schedule_collection = db[TRAINING_SCHEDULES_COLLECTION]
  schedule_workout = schedule_collection.find_one({ "date": {"$gte": twelve_hours_ago, "$lt": twelve_hours_from_now}})
  if schedule_workout is None:
    print "No workout found"
    exit()

  print "schedule_workout: %s" % schedule_workout
  print "Setting running goal to: %s" % schedule_workout['distance']
  update_metric_value(METRIC_ID, schedule_workout['distance'])


if __name__ == '__main__':
  main()


