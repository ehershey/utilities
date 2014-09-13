#!/usr/bin/env python
import datetime
import os
import os.path
import time
from os.path import expanduser
from numerousapp import update_metric_value, get_metric_value
home = expanduser("~ernie")


TEMPLATE_FILENAME = "%s/unit-report-template.html" % os.path.dirname(os.path.realpath(__file__))
MOVES_CSV_FILENAME = "%s/Dropbox/Web/moves.csv" % home

MIN_HOUR_FOR_ZERO_POST = 5

placeholder = {}

units_today = os.popen("cut -f5 -d, %s  | head -2 | tail -1" % MOVES_CSV_FILENAME).read().rstrip()
biked_today = os.popen("cut -f2 -d, %s  | head -2 | tail -1 | tr -d a-z" % MOVES_CSV_FILENAME).read().rstrip()
ran_today = os.popen("cut -f3 -d, %s  | head -2 | tail -1 | tr -d a-z" % MOVES_CSV_FILENAME).read().rstrip()
walked_today = os.popen("cut -f4 -d, %s  | head -2 | tail -1 | tr -d a-z" % MOVES_CSV_FILENAME).read().rstrip()
units_average = os.popen("cut -f5 -d, %s| awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_yesterday = os.popen("cut -f5 -d, %s  | head -3 | tail -1" % MOVES_CSV_FILENAME).read().rstrip()
units_average_2013 = os.popen("grep ^2013- %s | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_average_2014 = os.popen("grep ^2014- %s | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_average_7days = os.popen("head -8 %s | tail -7 | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_average_2days = os.popen("head -3 %s | tail -2 | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()


units_today_2013_diff = float(units_today) - float(units_average_2013)
units_yesterday_2013_diff = float(units_yesterday) - float(units_average_2013)
units_average_2013_diff = float(units_average) - float(units_average_2013)
units_average_7days_2013_diff = float(units_average_7days) - float(units_average_2013)
units_average_2days_2013_diff = float(units_average_2days) - float(units_average_2013)
units_average_2014_2013_diff = float(units_average_2014) - float(units_average_2013)

if units_today_2013_diff > 0:
    placeholder['today_class'] = "positive_diff"
else:
    placeholder['today_class'] = "negative_diff"

if units_yesterday_2013_diff > 0:
    placeholder['yesterday_class'] = "positive_diff"
else:
    placeholder['yesterday_class'] = "negative_diff"

if units_average_2days_2013_diff > 0:
    placeholder['2days_class'] = "positive_diff"
else:
    placeholder['2days_class'] = "negative_diff"

if units_average_7days_2013_diff > 0:
    placeholder['7days_class'] = "positive_diff"
else:
    placeholder['7days_class'] = "negative_diff"

if units_average_2014_2013_diff > 0:
    placeholder['2014_class'] = "positive_diff"
else:
    placeholder['2014_class'] = "negative_diff"

if units_average_2013_diff > 0:
    placeholder['alltime_class'] = "positive_diff"
else:
    placeholder['alltime_class'] = "negative_diff"


placeholder['units_today_2013_diff'] = units_today_2013_diff
placeholder['units_today'] = units_today
placeholder['units_yesterday_2013_diff'] = units_yesterday_2013_diff
placeholder['units_yesterday'] = units_yesterday
placeholder['units_average'] = units_average
placeholder['units_average_2013_diff'] = units_average_2013_diff
placeholder['units_average_2013'] = units_average_2013
placeholder['units_average_2014'] = units_average_2014
placeholder['units_average_2014_2013_diff'] = units_average_2014_2013_diff
placeholder['units_average_7days'] = units_average_7days
placeholder['units_average_7days_2013_diff'] = units_average_7days_2013_diff
placeholder['units_average_2days'] = units_average_2days
placeholder['units_average_2days_2013_diff'] = units_average_2days_2013_diff
placeholder['now'] = time.ctime()
placeholder['moves_csv_modified'] = time.ctime(os.path.getmtime(MOVES_CSV_FILENAME))


# echo "units_today: $units_today"
# echo "units_average: $units_average"
# echo "units_average_2013: $units_average_2013"
# echo "units_average_2014: $units_average_2014"
# echo "units_average_7days: $units_average_7days"



if __name__ == '__main__':

    with open (TEMPLATE_FILENAME, "r") as myfile:
          template=myfile.read()

    formated = template.format(**placeholder)
    print formated

    # Report to numerous
    #
    # TODO: move this out of report script
    #

    # Only post if we have data for today or it's been long enough that we should have data for today
    #
    if units_today > 0 or datetime.datetime.now().hour > MIN_HOUR_FOR_ZERO_POST:
      running_goal = get_metric_value(5818738672989877729)
      walking_goal = get_metric_value(7758304728227275179)
      biking_goal = get_metric_value(5595761423440323786)
      if ran_today == "" or ran_today == None:
          ran_today = 0
      if biked_today == "" or biked_today == None:
          biked_today = 0
      if walked_today == "" or walked_today == None:
          walked_today = 0
      if running_goal:
        running_goal = running_goal['value']
      else:
        running_goal = 0
      if walking_goal:
        walking_goal = walking_goal['value']
      else:
        walking_goal = 0
      if biking_goal:
        biking_goal = biking_goal['value']
      else:
        biking_goal = 0

      biked_today = float(biked_today)
      ran_today = float(ran_today)
      walked_today = float(walked_today)
      update_metric_value(8748753640388107935, running_goal - ran_today)
      update_metric_value(94526752002396912, walking_goal - walked_today)
      update_metric_value(111285933456617558, biking_goal - biked_today)
      #update_metric_value(6359390767342201980, units_yesterday, updated = "2014-06-15T23:59:59.000Z")
      update_metric_value(6359390767342201980, units_today)
      update_metric_value(7670190745339240677, biked_today)
      update_metric_value(3043034116976301897, walked_today)
      update_metric_value(3398081990673437243, ran_today)
      update_metric_value(5212351794073589044, units_today_2013_diff)
      update_metric_value(7170780739467042866, units_average_2days)
      update_metric_value(1242812163656294116, units_average_2days_2013_diff)
