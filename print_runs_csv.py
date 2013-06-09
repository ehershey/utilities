#!/usr/bin/python2.7
import json
import sys

workouts = json.load(sys.stdin)['result']['output']['workouts']

for workout in workouts:
  if 'run' in workout['workout_type_name'].lower() or 'run' in workout['workout_description'].lower() :
    print workout['workout_date'] + ',' + workout['distance']

