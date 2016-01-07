#!/usr/bin/env python
import argparse
import datetime
import os
import os.path
import pymongo
import re
import sys
import time
from os.path import expanduser
from numerousapp import update_metric_value, get_metric_value


parser = argparse.ArgumentParser(description='Generate calorie report')
parser.add_argument('-s', '--skip-numerous',
                    action='store_true', help="Don't post to Numerous")
args = parser.parse_args()

RUNNING_CALORIE_MULTIPLIER = 118
WALKING_CALORIE_MULTIPLIER = 100
CYCLING_CALORIE_MULTIPLIER = 43

resting_daily_calories = 1700

home = expanduser("~ernie")

connection = pymongo.Connection('localhost', 27017)
db = connection.ernie_org

today = datetime.datetime.now()
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

today_summary = db.nutrition_summary.find_one(
    {"date": today.strftime("%B %-d, %Y")})
yesterday_summary = db.nutrition_summary.find_one(
    {"date": yesterday.strftime("%B %-d, %Y")})

date_regex_2013 = re.compile(", 2013")
date_regex_2014 = re.compile(", 2014")
date_regex_2016 = re.compile(", 2016")

nutrition_2013_average = db.nutrition_summary.aggregate([{"$match": {"date": date_regex_2013}}, {
                                                        "$group": {"_id": "2013", "Average": {"$avg": "$calories_numeric"}}}])
nutrition_2014_average = db.nutrition_summary.aggregate([{"$match": {"date": date_regex_2014}}, {
                                                        "$group": {"_id": "2014", "Average": {"$avg": "$calories_numeric"}}}])
nutrition_2016_average = db.nutrition_summary.aggregate([{"$match": {"date": date_regex_2016}}, {
                                                        "$group": {"_id": "2016", "Average": {"$avg": "$calories_numeric"}}}])
nutrition_2016_total = db.nutrition_summary.aggregate([{"$match": {"date": date_regex_2016}}, {
                                                      "$group": {"_id": "2016", "Total": {"$sum": "$calories_numeric"}}}])

input_today_url = "#"
input_yesterday_url = "#"
input_today = 0
input_yesterday = 0
input_2013 = 0
input_today_2013_diff = 0
input_yesterday_2013_diff = 0
input_yesterday_2014_diff = 0
input_2014 = 0
input_today_2014_diff = 0
input_2014_2013_diff = 0
input_2013_2014_diff = 0
surplus_today = 0
surplus_yesterday = 0
surplus_2days = 0
surplus_2014 = 0
surplus_today_2014_diff = 0
surplus_yesterday_2014_diff = 0
surplus_2days_2014_diff = 0
surplus_2016_total = 0
input_2016 = 0
input_2016_total = 0
surplus_2016_2014_diff = 0

if today_summary and today_summary['Calories']:
    input_today = round(today_summary['calories_numeric'], 2)

if today_summary and today_summary['report_url']:
    input_today_url = today_summary['report_url']

if yesterday_summary and yesterday_summary['Calories']:
    input_yesterday = round(yesterday_summary['calories_numeric'], 2)

if yesterday_summary and yesterday_summary['report_url']:
    input_yesterday_url = yesterday_summary['report_url']


if nutrition_2013_average and nutrition_2013_average['result']:
    input_2013 = round(nutrition_2013_average['result'][0]['Average'], 2)

if nutrition_2014_average and nutrition_2014_average['result']:
    input_2014 = round(nutrition_2014_average['result'][0]['Average'], 2)

if nutrition_2016_average and nutrition_2016_average['result']:
    input_2016 = round(nutrition_2016_average['result'][0]['Average'], 2)

if nutrition_2016_total and nutrition_2016_total['result']:
    input_2016_total = round(nutrition_2016_total['result'][0]['Total'], 2)


input_today_2014_diff = round(input_2014 - input_today, 2)
input_today_2013_diff = round(input_2013 - input_today, 2)
input_yesterday_2013_diff = round(input_2013 - input_yesterday, 2)
input_yesterday_2014_diff = round(input_2014 - input_yesterday, 2)
input_2014_2013_diff = round(input_2013 - input_2014, 2)
input_2013_2014_diff = round(input_2014 - input_2013, 2)


TEMPLATE_FILENAME = "%s/unit-report-template.html" % os.path.dirname(
    os.path.realpath(__file__))
MOVES_CSV_FILENAME = "%s/Dropbox/Web/moves.csv" % home

MIN_HOUR_FOR_ZERO_POST = 5

placeholder = {}

sys.stderr.write("starting cuts\n")

units_today = os.popen("cut -f10 -d, %s  | head -2 | tail -1" %
                       MOVES_CSV_FILENAME).read().rstrip()
sys.stderr.write("in cuts 0.3\n")
biked_today = os.popen("cut -f3 -d, %s  | head -2 | tail -1 | tr -d a-z" %
                       MOVES_CSV_FILENAME).read().rstrip()
sys.stderr.write("in cuts 0.4\n")
ran_today = os.popen("cut -f5 -d, %s  | head -2 | tail -1 | tr -d a-z" %
                     MOVES_CSV_FILENAME).read().rstrip()
sys.stderr.write("in cuts 0.5\n")
walked_today = os.popen("cut -f2 -d, %s  | head -2 | tail -1 | tr -d a-z" %
                        MOVES_CSV_FILENAME).read().rstrip()
units_average = os.popen(
    "cut -f10 -d, %s| awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_yesterday = os.popen(
    "cut -f10 -d, %s  | head -3 | tail -1" % MOVES_CSV_FILENAME).read().rstrip()
sys.stderr.write("in cuts 1\n")
units_average_2013 = os.popen(
    "grep ^2013- %s | cut -f10 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_average_2014 = os.popen(
    "grep ^2014- %s | cut -f10 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_average_2016 = os.popen(
    "grep ^2016- %s | cut -f10 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_2016_total = os.popen(
    "grep ^2016- %s | cut -f10 -d, | awk '{ total += $1; count++ } END { print total }'" % MOVES_CSV_FILENAME).read().rstrip()
sys.stderr.write("in cuts 2\n")
day_count_2016 = os.popen(
    "grep ^2016- %s | cut -f10 -d, | awk '{ total += $1; count++ } END { print count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_average_7days = os.popen(
    "head -8 %s | tail -7 | cut -f10 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_average_2days = os.popen(
    "head -3 %s | tail -2 | cut -f10 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()

sys.stderr.write("done with cuts\n")

surplus_today = float(input_today) - \
    (float(units_today) + resting_daily_calories)
surplus_yesterday = float(input_yesterday) - \
    (float(units_yesterday) + resting_daily_calories)
surplus_2days = (surplus_today + surplus_yesterday) / 2
surplus_2014 = float(input_2014) - \
    (float(units_average_2014) + resting_daily_calories)
surplus_2016 = float(input_2016) - \
    (float(units_average_2016) + resting_daily_calories)
surplus_2016_total = float(input_2016_total) - (float(units_2016_total) +
                                                resting_daily_calories * int(day_count_2016))
surplus_2016_2014_diff = round(surplus_2016 - surplus_2014, 2)

surplus_today_2014_diff = round(surplus_2014 - surplus_today, 2)
surplus_yesterday_2014_diff = round(surplus_2014 - surplus_yesterday, 2)
surplus_2days_2014_diff = round(surplus_2014 - surplus_2days, 2)

units_today_2013_diff = float(units_today) - float(units_average_2013)
units_today_2014_diff = float(units_today) - float(units_average_2014)
units_yesterday_2013_diff = float(units_yesterday) - float(units_average_2013)
units_yesterday_2014_diff = float(units_yesterday) - float(units_average_2014)
units_average_2013_diff = float(units_average) - float(units_average_2013)
units_average_2014_diff = float(units_average) - float(units_average_2014)
units_average_7days_2013_diff = float(
    units_average_7days) - float(units_average_2013)
units_average_7days_2014_diff = float(
    units_average_7days) - float(units_average_2014)
units_average_2days_2013_diff = float(
    units_average_2days) - float(units_average_2013)
units_average_2days_2014_diff = float(
    units_average_2days) - float(units_average_2014)
units_average_2014_2013_diff = float(
    units_average_2014) - float(units_average_2013)
units_average_2013_2014_diff = float(
    units_average_2013) - float(units_average_2014)

minutes_since_moves_update = (datetime.datetime.now(
) - datetime.datetime.fromtimestamp(os.path.getmtime(MOVES_CSV_FILENAME))).seconds / 60

if units_today_2013_diff > 0:
    placeholder['today_class'] = "positive_diff"
else:
    placeholder['today_class'] = "negative_diff"

if surplus_today < surplus_2014:
    placeholder['surplus_class'] = "positive_diff"
else:
    placeholder['surplus_class'] = "negative_diff"

if surplus_2days < surplus_2014:
    placeholder['surplus_2days_class'] = "positive_diff"
else:
    placeholder['surplus_2days_class'] = "negative_diff"

if surplus_2016_2014_diff > 0:
    placeholder['surplus_2016_class'] = "negative_diff"
else:
    placeholder['surplus_2016_class'] = "positive_diff"

if input_today_2014_diff > 0:
    placeholder['input_class'] = "positive_diff"
else:
    placeholder['input_class'] = "negative_diff"

if units_average_2days_2013_diff > 0:
    placeholder['2days_class'] = "positive_diff"
else:
    placeholder['2days_class'] = "negative_diff"

if units_average_7days_2013_diff > 0:
    placeholder['7days_class'] = "positive_diff"
else:
    placeholder['7days_class'] = "negative_diff"

if units_average_2013_diff > 0:
    placeholder['alltime_class'] = "positive_diff"
else:
    placeholder['alltime_class'] = "negative_diff"


placeholder['units_today_2013_diff'] = units_today_2013_diff
placeholder['units_today_2014_diff'] = units_today_2014_diff
placeholder['units_today'] = units_today
placeholder['units_yesterday_2013_diff'] = units_yesterday_2013_diff
placeholder['units_yesterday_2014_diff'] = units_yesterday_2014_diff
placeholder['units_yesterday'] = units_yesterday
placeholder['units_average'] = units_average
placeholder['units_average_2013_diff'] = units_average_2013_diff
placeholder['units_average_2014_diff'] = units_average_2014_diff
placeholder['units_average_2013'] = units_average_2013
placeholder['units_average_2014'] = units_average_2014
placeholder['units_average_2014_2013_diff'] = units_average_2014_2013_diff
placeholder['units_average_2013_2014_diff'] = units_average_2013_2014_diff
placeholder['units_average_7days'] = units_average_7days
placeholder['units_average_7days_2013_diff'] = units_average_7days_2013_diff
placeholder['units_average_7days_2014_diff'] = units_average_7days_2014_diff
placeholder['units_average_2days'] = units_average_2days
placeholder['units_average_2days_2013_diff'] = units_average_2days_2013_diff
placeholder['units_average_2days_2014_diff'] = units_average_2days_2014_diff
placeholder['now'] = time.ctime()
placeholder['moves_csv_modified'] = time.ctime(
    os.path.getmtime(MOVES_CSV_FILENAME))
placeholder['input_today'] = input_today
placeholder['input_yesterday'] = input_yesterday
placeholder['input_today_2013_diff'] = input_today_2013_diff
placeholder['input_yesterday_2013_diff'] = input_yesterday_2013_diff
placeholder['input_yesterday_2014_diff'] = input_yesterday_2014_diff
placeholder['input_2014'] = input_2014
placeholder['input_today_2014_diff'] = input_today_2014_diff
placeholder['input_2014_2013_diff'] = input_2014_2013_diff
placeholder['input_2013_2014_diff'] = input_2013_2014_diff
placeholder['input_today_url'] = input_today_url
placeholder['input_yesterday_url'] = input_yesterday_url
placeholder['surplus_today'] = surplus_today
placeholder['surplus_2014'] = surplus_2014
placeholder['surplus_2016'] = surplus_2016
placeholder['surplus_yesterday'] = surplus_yesterday
placeholder['surplus_2days'] = surplus_2days
placeholder['surplus_today_2014_diff'] = surplus_today_2014_diff
placeholder['surplus_yesterday_2014_diff'] = surplus_yesterday_2014_diff
placeholder['surplus_2days_2014_diff'] = surplus_2days_2014_diff
placeholder['surplus_2016_2014_diff'] = surplus_2016_2014_diff
placeholder['surplus_2016_total'] = surplus_2016_total


# echo "units_today: $units_today"
# echo "units_average: $units_average"
# echo "units_average_2013: $units_average_2013"
# echo "units_average_2014: $units_average_2014"
# echo "units_average_7days: $units_average_7days"


if __name__ == '__main__':

    with open(TEMPLATE_FILENAME, "r") as myfile:
        template = myfile.read()

    formated = template.format(**placeholder)
    print formated

    # Report to numerous
    #
    # TODO: move this out of report script
    #

    # Only post if we have data for today or it's been long enough that we should have data for today
    #
    if not args.skip_numerous and (units_today > 0 or datetime.datetime.now().hour > MIN_HOUR_FOR_ZERO_POST):
        running_goal = get_metric_value(5818738672989877729)
        walking_goal = get_metric_value(7758304728227275179)
        biking_goal = get_metric_value(5595761423440323786)
        if ran_today == "" or not ran_today:
            ran_today = 0
        if biked_today == "" or not biked_today:
            biked_today = 0
        if walked_today == "" or not walked_today:
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
        # update_metric_value(6359390767342201980, units_yesterday, updated = "2014-06-15T23:59:59.000Z")
        update_metric_value(6359390767342201980, units_today)
        update_metric_value(7670190745339240677, biked_today)
        update_metric_value(3043034116976301897, walked_today)
        update_metric_value(3398081990673437243, ran_today)
        update_metric_value(5212351794073589044, units_today_2013_diff)
        update_metric_value(7170780739467042866, units_average_2days)
        update_metric_value(1242812163656294116, units_average_2days_2013_diff)
        update_metric_value(3766962275739755372, minutes_since_moves_update)


def get_daily_calorie_goal():
    return float(units_average_2013)


def get_running_calorie_multiplier():
    return RUNNING_CALORIE_MULTIPLIER


def get_cycling_calorie_multiplier():
    return CYCLING_CALORIE_MULTIPLIER


def get_walking_calorie_multiplier():
    return WALKING_CALORIE_MULTIPLIER
