#!/usr/bin/python2.7
# print_moves_csv.py
#
# Format moves json (from https://api.moves-app.com/) into csv
#
# 
import datetime
import json
import os.path
import re
import sys
import subprocess


verbose_activity_names = {
    "wlk": "Walking",
    "run": "Running",
    "cyc": "Cycling"
    }

sys.stdout.write("Date")
for activity_name,verbose_activity_name in verbose_activity_names.items():
  sys.stdout.write(",")
  sys.stdout.write(verbose_activity_name)
sys.stdout.write("\n")

def print_workouts_from_json_stream(instream):
  output = json.load(instream)

  for index, summary in enumerate(output):
    activities = summary['summary']
    sys.stdout.write(str(datetime.datetime.strptime(summary['date'],'%Y%m%d')))
    activities_by_name = {}
    if activities:
      for activity in activities:
        activities_by_name[activity['activity']] = activity
    for activity_name in verbose_activity_names:
      sys.stdout.write(",")
      if activity_name in activities_by_name:
        sys.stdout.write(str(activity['distance']))
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

