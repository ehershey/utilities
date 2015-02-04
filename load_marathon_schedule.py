#!/usr/bin/env python
# 
# Given the date of a marathon, backfill a training schedule with training plan
# culminating on the date of the marathon. 
#
# This depends on having a "training_plans" collection populated by the populating 
# script, available here: 
# https://github.com/ehershey/utilities/blob/master/nike_training_plan_to_mongodb.sh
# 
#
import argparse
import datetime
import dateutil.parser
from pymongo import MongoClient, DESCENDING
import uuid

DB = "ernie_org"
TRAINING_PLANS_COLLECTION = "training_plan"
TRAINING_SCHEDULES_COLLECTION = "training_schedule"
ACTIVITY_TYPE='Running'

EVENT_DISTANCE = 26.2

parser = argparse.ArgumentParser(description='Load Marathon Training Schedule')
parser.add_argument('marathon_date', help='Date of marathon')
parser.add_argument('--level', help='Training Plan Level', type=int, choices=[1,2,3], default = 3)
args = parser.parse_args()

client = MongoClient('localhost', 27017)
db = client[DB]

load_uuid = uuid.uuid4()

plan_collection = db[TRAINING_PLANS_COLLECTION]
schedule_collection = db[TRAINING_SCHEDULES_COLLECTION]
plan_workouts = plan_collection.find({ "level": args.level}).sort([ ("day", DESCENDING )])

if plan_workouts.count() == 0:
    print "No training plans found (need to run nike_training_plan_to_mongodb.sh?)"
    exit()

found_event = False
days_from_event = 0

# Set time on date object to noon to account for timezone differences
#
event_date = dateutil.parser.parse(args.marathon_date).replace(hour=12)

insert_total = 0

for plan_workout in plan_workouts:
  schedule_workout = None
  distance = plan_workout['distance']
  if distance == EVENT_DISTANCE:
    found_event = True
    schedule_workout = plan_workout
    schedule_workout['date'] = event_date
  elif found_event:
    days_from_event = days_from_event + 1
    schedule_date = event_date - datetime.timedelta(days=days_from_event)
    schedule_workout = plan_workout
    schedule_workout['date'] = schedule_date
  if schedule_workout:
    # Remove _id from plan document
    # 
    del(schedule_workout['_id'])
    schedule_workout['activity_type'] = ACTIVITY_TYPE
    schedule_workout['load_uuid'] = load_uuid


    result = schedule_collection.update({ "date": schedule_workout['date'], "activity_type": ACTIVITY_TYPE }, schedule_workout, upsert = True)
    if not result['updatedExisting']:
      insert_total = insert_total +1

print "Inserted %s total schedule entries" % insert_total
