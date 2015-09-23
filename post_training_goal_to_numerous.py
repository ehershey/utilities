#!/usr/bin/env python
# vim: set filetype=python expandtab ai smartindent:
#
# Post training goals for the day to Numerous
#

import datetime
from numerousapp import update_metric_value, get_metric_value
from pymongo import MongoClient
from unit_report import (get_daily_calorie_goal,
                         get_running_calorie_multiplier,
                         get_cycling_calorie_multiplier,
                         get_walking_calorie_multiplier)

DB = "ernie_org"
TRAINING_SCHEDULES_COLLECTION = "training_schedule"
ACTIVITY_TYPE = 'Running'

RUNNING_METRIC_ID = 5818738672989877729
WALKING_METRIC_ID = 7758304728227275179
CYCLING_METRIC_ID = 5595761423440323786


def main():

    today = datetime.datetime.now().replace(
        hour=12, minute=0, second=0, microsecond=0)
    twelve_hours_ago = today - datetime.timedelta(hours=12)
    twelve_hours_from_now = today + datetime.timedelta(hours=12)

    print "twelve_hours_ago: " + str(twelve_hours_ago)
    print "twelve_hours_from_now: " + str(twelve_hours_from_now)

    client = MongoClient('localhost', 27017)
    db = client[DB]

    schedule_collection = db[TRAINING_SCHEDULES_COLLECTION]
    schedule_workout = schedule_collection.find_one(
        {"date": {"$gte": twelve_hours_ago, "$lt": twelve_hours_from_now}})
    if schedule_workout:
        running_goal_distance = schedule_workout['distance']
    else:
        print "No workout found"
        print "Using 0 distance"
        running_goal_distance = 0
    print "schedule_workout: %s" % schedule_workout
    print "Setting running goal to: %s" % running_goal_distance
    walking_goal_distance = get_metric_value(WALKING_METRIC_ID).get('value')
    print "walking_goal_distance: %s" % walking_goal_distance

    daily_calorie_goal = get_daily_calorie_goal()
    running_calorie_multiplier = get_running_calorie_multiplier()
    walking_calorie_multiplier = get_walking_calorie_multiplier()
    cycling_calorie_multiplier = get_cycling_calorie_multiplier()
    running_calorie_goal = running_goal_distance * running_calorie_multiplier
    walking_calorie_goal = walking_goal_distance * walking_calorie_multiplier
    covered_calorie_goal = running_calorie_goal + walking_calorie_goal
    cycling_calorie_goal = daily_calorie_goal - covered_calorie_goal
    cycling_goal_distance = cycling_calorie_goal / cycling_calorie_multiplier

    print "Setting cycling goal to: %s" % cycling_goal_distance

    update_metric_value(RUNNING_METRIC_ID, running_goal_distance)
    update_metric_value(CYCLING_METRIC_ID, cycling_goal_distance)


if __name__ == '__main__':
    main()
