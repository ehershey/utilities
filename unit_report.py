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


parser = argparse.ArgumentParser(description='Generate calorie report')
args = parser.parse_args()

RUNNING_CALORIE_MULTIPLIER = 118
WALKING_CALORIE_MULTIPLIER = 100
CYCLING_CALORIE_MULTIPLIER = 43

resting_daily_calories = 1700

home = expanduser("~ernie")

#connection = pymongo.Connection('localhost', 27017)
#db = connection.ernie_org
client = pymongo.MongoClient("mongodb://localhost:27017")
database = client.get_database("ernie_org")
nutrition_summary_collection = database.get_collection("nutrition_summary")

today = datetime.datetime.now()
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

current_year = today.year
previous_year = current_year - 1

current_month = today.month
previous_month = current_month - 1

current_day = today.day
previous_day = current_day - 1

# zero padding
#
# current_month = "%02d" % (current_month)
# previous_month = "%02d" % (previous_month)

# current_day = "%02d" % (current_day)
# previous_day = "%02d" % (previous_day)

today_summary = nutrition_summary_collection.find_one(
    {"date": today.strftime("%B %-d, %Y")})
yesterday_summary = nutrition_summary_collection.find_one(
    {"date": yesterday.strftime("%B %-d, %Y")})

date_regex_previous_year = re.compile(", %d".format(previous_year))
date_regex_current_year = re.compile(", %d".format(current_year))

nutrition_previous_year_average = nutrition_summary_collection.aggregate([{"$match": {"date": date_regex_previous_year}}, {
                                                        "$group": {"_id": str(previous_year), "Average": {"$avg": "$calories_numeric"}}}])
nutrition_current_year_average = nutrition_summary_collection.aggregate([{"$match": {"date": date_regex_current_year}}, {
                                                        "$group": {"_id": str(current_year), "Average": {"$avg": "$calories_numeric"}}}])
nutrition_current_year_total = nutrition_summary_collection.aggregate([{"$match": {"date": date_regex_current_year}}, {
                                                      "$group": {"_id": str(current_year), "Total": {"$sum": "$calories_numeric"}}}])

TEMPLATE_FILENAME = "%s/unit-report-template.html" % os.path.dirname(
    os.path.realpath(__file__))
MOVES_CSV_FILENAME = "%s/Dropbox/Web/moves.csv" % home

MIN_HOUR_FOR_ZERO_POST = 5

placeholder = {}

sys.stderr.write("starting cuts\n")

units_today = os.popen("sed 's/.*,//' %s  | head -2 | tail -1" %
                       MOVES_CSV_FILENAME).read().rstrip()
sys.stderr.write("in cuts 0.3\n")
biked_today_cmd = "cut -f3 -d, %s  | head -2 | tail -1 | tr -d a-z" % MOVES_CSV_FILENAME
sys.stderr.write("in cuts 0.3, cmd: %s\n" % biked_today_cmd)
biked_today = os.popen(biked_today_cmd).read().rstrip()
sys.stderr.write("in cuts 0.3, cmd: %s\n" % biked_today_cmd)
sys.stderr.write("in cuts 0.4\n")
ran_today = os.popen("cut -f5 -d, %s  | head -2 | tail -1 | tr -d a-z" %
                     MOVES_CSV_FILENAME).read().rstrip()
sys.stderr.write("in cuts 0.5\n")
walked_today = os.popen("cut -f2 -d, %s  | head -2 | tail -1 | tr -d a-z" %
                        MOVES_CSV_FILENAME).read().rstrip()
units_average = os.popen(
    "sed 's/.*,//' %s| awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_yesterday = os.popen(
    "sed 's/.*,//' %s  | head -3 | tail -1" % MOVES_CSV_FILENAME).read().rstrip()

sys.stderr.write("cmd: grep ^%d-%02d-%02d %s | sed 's/.*,//' \n" % (previous_year, current_month, current_day, MOVES_CSV_FILENAME))
units_today_last_year = os.popen(
    "grep ^%d-%02d-%02d %s | sed 's/.*,//' " % (previous_year, current_month, current_day, MOVES_CSV_FILENAME)).read().rstrip()
sys.stderr.write("in cuts 1\n")
units_average_previous_year = os.popen(
    "grep ^%d- %s | sed 's/.*,//' | awk '{ total += $1; count++ } END { print total/count }'" % (previous_year, MOVES_CSV_FILENAME)).read().rstrip()
units_average_current_year = os.popen(
    "grep ^%d- %s | sed 's/.*,//' | awk '{ total += $1; count++ } END { print total/count }'" % (current_year, MOVES_CSV_FILENAME)).read().rstrip()
units_current_year_total = os.popen(
    "grep ^%d- %s | sed 's/.*,//' | awk '{ total += $1; count++ } END { print total }'" % (current_year, MOVES_CSV_FILENAME)).read().rstrip()
sys.stderr.write("in cuts 2\n")
day_count_current_year = os.popen(
    "grep ^%d- %s | sed 's/.*,//' | awk '{ total += $1; count++ } END { print count }'" % (current_year, MOVES_CSV_FILENAME)).read().rstrip()
units_average_30days = os.popen(
    "head -8 %s | tail -30 | sed 's/.*,//' | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_average_7days = os.popen(
    "head -8 %s | tail -7 | sed 's/.*,//' | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_average_2days = os.popen(
    "head -3 %s | tail -2 | sed 's/.*,//' | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()

sys.stderr.write("done with cuts\n")

if not units_today_last_year:
    units_today_last_year = "0"

units_today_previous_year_diff = float(units_today) - float(units_average_previous_year)
units_yesterday_previous_year_diff = float(units_yesterday) - float(units_average_previous_year)
units_average_previous_year_diff = float(units_average) - float(units_average_previous_year)
units_average_7days_previous_year_diff = float(
    units_average_7days) - float(units_average_previous_year)
units_average_30days_previous_year_diff = float(
    units_average_30days) - float(units_average_previous_year)
units_average_2days_previous_year_diff = float(
    units_average_2days) - float(units_average_previous_year)
units_average_current_year_previous_year_diff = float(
    units_average_current_year) - float(units_average_previous_year)
sys.stderr.write('utly: ' + units_today_last_year + "\n")
sys.stderr.write('uapy: ' + units_average_previous_year + "\n")
sys.stderr.write("units_today_last_year: {0}\n".format(units_today_last_year))
units_today_last_year_previous_year_diff = float(units_today_last_year) - float(units_average_previous_year)

units_today_30days_diff = float(units_today) - float(units_average_30days)
units_yesterday_30days_diff = float(units_yesterday) - float(units_average_30days)
units_average_30days_diff = float(units_average) - float(units_average_30days)
units_average_7days_30days_diff = float(
    units_average_7days) - float(units_average_30days)
units_average_2days_30days_diff = float(
    units_average_2days) - float(units_average_30days)
units_average_current_year_30days_diff = float(
    units_average_current_year) - float(units_average_30days)
units_average_previous_year_30days_diff = float(
    units_average_previous_year) - float(units_average_30days)
units_today_last_year_30days_diff = float(units_today_last_year) - float(units_average_30days)

minutes_since_moves_update = (datetime.datetime.now(
) - datetime.datetime.fromtimestamp(os.path.getmtime(MOVES_CSV_FILENAME))).seconds / 60

placeholder['units_today'] = units_today
placeholder['units_today_last_year'] = units_today_last_year
placeholder['units_yesterday'] = units_yesterday
placeholder['units_average'] = units_average
placeholder['units_average_30days'] = units_average_30days
placeholder['units_average_previous_year'] = units_average_previous_year
placeholder['units_average_7days'] = units_average_7days
placeholder['units_average_2days'] = units_average_2days
placeholder['now'] = time.ctime()
placeholder['moves_csv_modified'] = time.ctime(
    os.path.getmtime(MOVES_CSV_FILENAME))
placeholder['units_average_current_year'] = units_average_current_year

placeholder['units_today_previous_year_diff'] = units_today_previous_year_diff
placeholder['units_today_last_year_previous_year_diff'] = units_today_last_year_previous_year_diff
placeholder['units_yesterday_previous_year_diff'] = units_yesterday_previous_year_diff
placeholder['units_average_previous_year_diff'] = units_average_previous_year_diff
placeholder['units_average_7days_previous_year_diff'] = units_average_7days_previous_year_diff
placeholder['units_average_30days_previous_year_diff'] = units_average_30days_previous_year_diff
placeholder['units_average_2days_previous_year_diff'] = units_average_2days_previous_year_diff
placeholder['units_average_current_year_previous_year_diff'] = units_average_current_year_previous_year_diff

placeholder['units_today_30days_diff'] = units_today_30days_diff
placeholder['units_today_last_year_30days_diff'] = units_today_last_year_30days_diff
placeholder['units_yesterday_30days_diff'] = units_yesterday_30days_diff
placeholder['units_average_30days_diff'] = units_average_30days_diff
placeholder['units_average_7days_30days_diff'] = units_average_7days_30days_diff
placeholder['units_average_2days_30days_diff'] = units_average_2days_30days_diff
placeholder['units_average_current_year_30days_diff'] = units_average_current_year_30days_diff
placeholder['units_average_previous_year_30days_diff'] = units_average_previous_year_30days_diff

placeholder['current_year'] = current_year
placeholder['previous_year'] = previous_year
placeholder['today_class'] = ""
placeholder['2days_class'] = ""
placeholder['7days_class'] = ""
placeholder['alltime_class'] = ""

if __name__ == '__main__':

    with open(TEMPLATE_FILENAME, "r") as myfile:
        template = myfile.read()

    formated = template.format(**placeholder)
    print formated


def get_running_calorie_multiplier():
    return RUNNING_CALORIE_MULTIPLIER


def get_cycling_calorie_multiplier():
    return CYCLING_CALORIE_MULTIPLIER


def get_walking_calorie_multiplier():
    return WALKING_CALORIE_MULTIPLIER
