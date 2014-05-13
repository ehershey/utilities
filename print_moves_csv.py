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
    "cyc": "Cycling"
    }

sys.stdout.write("Date")
for activity_name, verbose_activity_name in sorted(verbose_activity_names.items()):
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
    activities_by_name = {}
    calories = 0
    if activities:
      for activity in activities:
        activities_by_name[activity['activity']] = activity
        calories += activity['calories']
    for activity_name in sorted(verbose_activity_names):
      sys.stdout.write(",")
      if activity_name in activities_by_name:
        distance_meters = activities_by_name[activity_name]['distance']
        distance_miles = distance_meters / METERS_IN_ONE_MILE
        sys.stdout.write("%.2fmi" % distance_miles)
    sys.stdout.write(",%d" % calories)
    sys.stdout.write("\n")

#  if output.has_key('workouts'):
#    workouts = output['workouts']
#  elif output.has_key('workout'):
#    workouts = output['workout']['children']
#  else:
#    raise "Can't find workout list in results"
#
#  for workout in workouts:
#    if 'run' in workout['workout_type_name'].lower() or 'run' in workout['workout_description'].lower() :
#      # adjust date if format is weird
#      #
#      workout_date = re.sub(r'(\d+)/(\d+)/(\d+)',r'\3-\1-\2',workout['workout_date'])
#      print workout_date + ',' + workout['distance']
#    if 'multi' in workout['workout_type_name'].lower() or 'multi' in workout['workout_description'].lower() :
#      # print 'need to get more info based on ' + workout['workout_type_name'] + ',' + workout['workout_description'] + ',' + workout['workout_id']
#      process = subprocess.Popen([os.path.dirname(__file__) + "/mapmyfitness.py","http://api.mapmyfitness.com/3.1/workouts/get_workout_full?workout_id=" + workout['workout_id']], stdout = subprocess.PIPE);
#
#      print_workouts_from_json_stream(process.stdout)
#      #print process.stdout.read()

print_workouts_from_json_stream(sys.stdin)


#str(datetime.datetime.strptime(summs[0]['date'],'%Y%m%d'))
#Out[24]: '2013-07-29 00:00:00'
#
#In [25]: summs
#Out[25]:
#[{u'caloriesIdle': 1773,
#  u'date': u'20130729',
#  u'summary': [{u'activity': u'wlk',
#    u'calories': 128,
#    u'distance': 2079.0,
#    u'duration': 1699.0,
#    u'steps': 2665},
#   {u'activity': u'run',
#    u'calories': 1287,
#    u'distance': 17288.0,
#    u'duration': 6117.0,
#    u'steps': 15641},
#   {u'activity': u'cyc',
#    u'calories': 416,
#    u'distance': 15356.0,
#    u'duration': 2812.0}]},
# {u'caloriesIdle': 1773,
#  u'date': u'20130730',
#  u'summary': [{u'activity': u'wlk',
#    u'calories': 121,

