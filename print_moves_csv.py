#!/usr/bin/python
# print_moves_csv.py
#
# Format moves json (from https://api.moves-app.com/) into csv
#
# Example usage:
# */2 * * * * curl "https://api.moves-app.com/api/v1/user/summary/daily?pastDays=10&access_token=$MOVES_ACCESS_TOKEN" | /home/ernie/git/utilities/print_moves_csv.py > /tmp/moves-new.csv ; touch /home/ernie/Dropbox/Web/moves.csv ; cat /home/ernie/Dropbox/Web/moves.csv >> /tmp/moves-new.csv ; cat /tmp/moves-new.csv   | sort  --reverse  | sort --key=1,1 --field-separator=, --reverse --unique > /home/ernie/Dropbox/Web/moves.csv
#
#
#
import datetime
import simplejson as json
import time
import os.path
import re
import sys
import subprocess

METERS_IN_ONE_MILE = 1609.34

verbose_activity_names = {
    "wlk": "Walking",
    "run": "Running",
    "cyc": "Cycling",
    "walking": "Walking",
    "running": "Running",
    "cycling": "Cycling",
    "swimming": "Swimming",
    "car": "Car",
    "transport": "Transport",
    "airplane": "Airplane"
    }

UNKNOWN_ACTIVITY_BUCKET_VERBOSE_NAME = "Unknown"

verbose_activity_name_list = list(set(sorted(verbose_activity_names.values())))

verbose_activity_name_list.append(UNKNOWN_ACTIVITY_BUCKET_VERBOSE_NAME)


sys.stdout.write("Date")
for verbose_activity_name in verbose_activity_name_list:
  sys.stdout.write(",")
  sys.stdout.write(verbose_activity_name)
sys.stdout.write(",Calories\n")

if hasattr(datetime.datetime, 'strptime'):
    #python 2.6
    strptime = datetime.datetime.strptime
else:
    #python 2.4 equivalent
    strptime = lambda date_string, format: datetime.datetime(*(time.strptime(date_string, format)[0:6]))


def print_workouts_from_json_stream(instream):
  output = json.load(instream)

  for index, summary in enumerate(output):
    activities = summary['summary']
    sys.stdout.write(str(strptime(summary['date'], '%Y%m%d')))
    activities_by_verbose_name = {}
    calories = 0
    if activities:
      for activity in activities:
        verbose_activity_name = verbose_activity_names.get(activity['activity'])
        if not verbose_activity_name:
          verbose_activity_name = UNKNOWN_ACTIVITY_BUCKET_VERBOSE_NAME
        activities_by_verbose_name[verbose_activity_name] = activity
        activity_calories = activity.get('calories')
        if activity_calories:
          calories += activity_calories
    for verbose_activity_name in verbose_activity_name_list:
      sys.stdout.write(",")
      if verbose_activity_name in activities_by_verbose_name:
        distance_meters = activities_by_verbose_name[verbose_activity_name].get('distance')
        if distance_meters:
          distance_miles = distance_meters / METERS_IN_ONE_MILE
        else:
          distance_miles = 0
        sys.stdout.write("%.2fmi" % distance_miles)
    sys.stdout.write(",%d" % calories)
    sys.stdout.write("\n")

print_workouts_from_json_stream(sys.stdin)
