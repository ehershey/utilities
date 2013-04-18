#!/usr/bin/python2.7
import json
import sys

workouts = json.load(sys.stdin)['result']['output']['workouts']

for workout in workouts:
  if 'Run' in workout['workout_type_name'] or 'Run' in workout['workout_description'] :
    print workout['workout_date'] + ',' + workout['distance']

