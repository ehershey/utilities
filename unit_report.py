#!/usr/bin/env python
#
# Output calorie report based on moves data in database
# Requires $MOVES_ACCESS_TOKEN and MONGODB_URI environment variables
#
import argparse
import datetime
import dateutil.parser
import os
import os.path
from pymongo import MongoClient
import sys
import time
from os.path import expanduser

COLLECTION = "summaries"
DB = "moves"


parser = argparse.ArgumentParser(description='Generate calorie report')
parser.add_argument('--for-date', help='Date to generate report for', required = False)
args = parser.parse_args()

RUNNING_CALORIE_MULTIPLIER = 118
WALKING_CALORIE_MULTIPLIER = 100
CYCLING_CALORIE_MULTIPLIER = 43

resting_daily_calories = 1700

home = expanduser("~ernie")

if "MOVES_ACCESS_TOKEN" not in os.environ:
    raise Exception("No $MOVES_ACCESS_TOKEN defined.")
if "MONGODB_URI" not in os.environ:
    raise Exception("No $MONGODB_URI defined.")
MOVES_ACCESS_TOKEN = os.environ["MOVES_ACCESS_TOKEN"]
MONGODB_URI = os.environ["MONGODB_URI"]

client = MongoClient(MONGODB_URI)

db = client[DB]

collection = db[COLLECTION]

if args.for_date:
    today = dateutil.parser.parse(args.for_date).replace(hour=12)
else:
    today = datetime.datetime.now()

yesterday = today - datetime.timedelta(days=1)
day_before_yesterday = yesterday - datetime.timedelta(days=1)

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

TEMPLATE_FILENAME = "%s/unit-report-template.html" % os.path.dirname(
    os.path.realpath(__file__))
MOVES_CSV_FILENAME = "%s/Dropbox/Web/moves.csv" % home

MIN_HOUR_FOR_ZERO_POST = 5

placeholder = {}

sys.stderr.write("starting cuts\n")

today_summary = collection.find_one({"$and": [{"Date": {"$lte": today}}, {"Date": {"$gt": yesterday}} ]})

if today_summary:
    units_today = ("%d" % today_summary['Calories'])
else:
    units_today = 0

sys.stderr.write("units_today from db: {0}\n".format(units_today))


units_average_cursor = collection.aggregate([{"$group": {"_id": None, "average": { "$avg": "$Calories" } } } ] );

try:
    units_average_result = units_average_cursor.next()
    units_average = units_average_result['average']
except StopIteration as e:
    units_average = 0

sys.stderr.write("units_average from db: {0}\n".format(units_average))

units_yesterday = os.popen(
    "sed 's/.*,//' %s  | head -3 | tail -1" % MOVES_CSV_FILENAME).read().rstrip()

sys.stderr.write("units_yesterday from csv: {0}\n".format(units_yesterday))

yesterday_summary = collection.find_one({"$and": [{"Date": {"$lte": yesterday}}, {"Date": {"$gt": day_before_yesterday}} ]})

if yesterday_summary:
    units_yesterday = ("%d" % yesterday_summary['Calories'])
else:
    units_yesterday = 0

sys.stderr.write("units_yesterday from db: {0}\n".format(units_yesterday))

sys.stderr.write("cmd: grep ^%d-%02d-%02d %s | sed 's/.*,//' \n" % (previous_year, current_month, current_day, MOVES_CSV_FILENAME))
units_today_last_year = os.popen(
    "grep ^%d-%02d-%02d %s | sed 's/.*,//' " % (previous_year, current_month, current_day, MOVES_CSV_FILENAME)).read().rstrip()
sys.stderr.write("in cuts 1\n")
sys.stderr.write("cmd: grep ^%d- %s | sed 's/.*,//' | awk '{ total += $1; count++ } END { print total/count }'" % (previous_year, MOVES_CSV_FILENAME))
units_average_previous_year = os.popen(
    "grep ^%d- %s | sed 's/.*,//' | awk '{ total += $1; count++ } END { print total/count }'" % (previous_year, MOVES_CSV_FILENAME)).read().rstrip()
sys.stderr.write("in cuts 1.1\n")
units_average_current_year = os.popen(
    "grep ^%d- %s | sed 's/.*,//' | awk '{ total += $1; count++ } END { print total/count }'" % (current_year, MOVES_CSV_FILENAME)).read().rstrip()
sys.stderr.write("in cuts 1.2\n")
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

if not units_average_previous_year:
    units_average_previous_year = "0"

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
