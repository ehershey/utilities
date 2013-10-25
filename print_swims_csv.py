#!/usr/bin/python2.7
import json
import os.path
import re
import sys
import subprocess


def print_workouts_from_json_stream(instream):
  output = json.load(instream)['result']['output']
  if output.has_key('workouts'):
    workouts = output['workouts']
  elif output.has_key('workout'):
    workouts = output['workout']['children']
  else:
    raise "Can't find workout list in results"

  for workout in workouts:
    if 'swim' in workout['workout_type_name'].lower() or 'swim' in workout['workout_description'].lower():
      # adjust date if format is weird
      #
      workout_date = re.sub(r'(\d+)/(\d+)/(\d+)', r'\3-\1-\2', workout['workout_date'])
      print workout_date + ',' + workout['distance']
    if 'multi' in workout['workout_type_name'].lower() or 'multi' in workout['workout_description'].lower():
      # print 'need to get more info based on ' + workout['workout_type_name'] + ',' + workout['workout_description'] + ',' + workout['workout_id']
      process = subprocess.Popen([os.path.dirname(__file__) + "/mapmyfitness.py", "http://api.mapmyfitness.com/3.1/workouts/get_workout_full?workout_id=" + workout['workout_id']], stdout = subprocess.PIPE);

      print_workouts_from_json_stream(process.stdout)
      #print process.stdout.read()

print_workouts_from_json_stream(sys.stdin)
