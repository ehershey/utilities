#!/usr/bin/env python2.7
#
# Output calorie report based on moves data in database
# Requires MONGODB_URI environment variable
#
import argparse
import datetime
from datetime import timedelta
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
parser.add_argument('--for-date', help='Date to generate report for', required=False)

RUNNING_CALORIE_MULTIPLIER = 118
WALKING_CALORIE_MULTIPLIER = 100
CYCLING_CALORIE_MULTIPLIER = 43

resting_daily_calories = 1700

home = expanduser("~ernie")

TEMPLATE_FILENAME = "%s/unit-report-template.html" % os.path.dirname(
    os.path.realpath(__file__))
MOVES_CSV_FILENAME = "%s/Dropbox/Web/moves.csv" % home

placeholder = {}

if "MONGODB_URI" not in os.environ:
    raise Exception("No $MONGODB_URI defined.")
MONGODB_URI = os.environ["MONGODB_URI"]


def get_running_calorie_multiplier():
    return RUNNING_CALORIE_MULTIPLIER


def get_cycling_calorie_multiplier():
    return CYCLING_CALORIE_MULTIPLIER


def get_walking_calorie_multiplier():
    return WALKING_CALORIE_MULTIPLIER


def get_units_average(collection, forever_ago=datetime.datetime.now() - timedelta(days=50 * 365), today=datetime.datetime.now()):

    return int(get_average_between_two_dates(collection, forever_ago, today))
    units_average_cursor = collection.aggregate([{"$group": {"_id": None, "average": {"$avg": "$Calories"}}}])

    try:
        units_average_result = units_average_cursor.next()
        units_average = units_average_result['average']
    except StopIteration as e:
        units_average = 0
    return units_average


def get_average_between_two_dates(collection, min_date, max_date):

    match = {"$match": {"$and": [{"Date": {"$lte": max_date}}, {"Date": {"$gt": min_date}}]}}
    group = {"$group": {"_id": None, "average": {"$avg": "$Calories"}}}
    # sys.stderr.write("match: " + str(match) + "\n")
    # sys.stderr.write("group: " + str(group) + "\n")
    cursor = collection.aggregate([match, group])

    try:
        result = cursor.next()
        average = result['average']
    except StopIteration as e:
        average = 0
    return average


def get_7day_average(collection, today=datetime.datetime.now()):
    return int(get_average_between_two_dates(collection, today - timedelta(days=7), today))


def get_2day_average(collection, today=datetime.datetime.now()):
    return int(get_average_between_two_dates(collection, today - timedelta(days=2), today))


def get_30day_average(collection, today=datetime.datetime.now()):
    return int(get_average_between_two_dates(collection, today - timedelta(days=30), today))


def get_units_today(collection, yesterday=datetime.datetime.now() - timedelta(days=1), today=datetime.datetime.now()):
    units_today = int(get_average_between_two_dates(collection, yesterday, today))
    return units_today


def get_units_average_current_year(collection, today=datetime.datetime.now()):
    last_day_of_previous_year = get_last_day_of_previous_year(today=today)
    last_day_of_current_year = get_last_day_of_current_year(today=today)
    units_average_current_year = int(get_average_between_two_dates(collection, last_day_of_previous_year, last_day_of_current_year))
    return units_average_current_year


def get_last_day_of_previous_year(today=datetime.datetime.now()):
    # use last day of last year to account for db dates being 00:00, so anything > last day of last year
    # will only include this year

    last_day_of_previous_year = today.replace(month=1, day=1) - timedelta(days=1)
    return last_day_of_previous_year


def get_last_day_of_current_year(today=datetime.datetime.now()):
    last_day_of_current_year = today.replace(month=12, day=31)
    return last_day_of_current_year


if __name__ == '__main__':

    client = MongoClient(MONGODB_URI)

    db = client[DB]

    collection = db[COLLECTION]

    args = parser.parse_args()
    if args.for_date:
        today = dateutil.parser.parse(args.for_date).replace(hour=12)
    else:
        today = datetime.datetime.now()

    forever_ago = today - timedelta(days=50 * 365)
    yesterday = today - timedelta(days=1)
    day_before_yesterday = yesterday - timedelta(days=1)

    current_year = today.year
    previous_year = current_year - 1

    current_month = today.month
    previous_month = current_month - 1

    current_day = today.day
    previous_day = current_day - 1

    today_last_year = today.replace(year=previous_year)
    yesterday_last_year = today_last_year - timedelta(days=1)

    units_today = get_units_today(collection, yesterday, today)

    units_average = get_units_average(collection)

    units_yesterday = int(get_average_between_two_dates(collection, day_before_yesterday, yesterday))

    units_today_last_year = int(get_average_between_two_dates(collection, yesterday_last_year, today_last_year))

    # use last day of two years ago to account for db dates being 00:00, so anything > last day of two years ago
    # will only include last year, not two years ago

    last_day_of_year_before_previous_year = today_last_year.replace(month=1, day=1) - timedelta(days=1)

    last_day_of_previous_year = get_last_day_of_previous_year(today=today)

    units_average_previous_year = int(get_average_between_two_dates(collection, last_day_of_year_before_previous_year, last_day_of_previous_year))

    units_average_current_year = get_units_average_current_year(collection, today=today)

    units_average_7days = get_7day_average(collection, today)
    units_average_2days = get_2day_average(collection, today)
    units_average_30days = get_30day_average(collection, today)
    units_today_previous_year_diff = units_today - units_average_previous_year
    units_yesterday_previous_year_diff = units_yesterday - units_average_previous_year
    units_average_previous_year_diff = units_average - units_average_previous_year
    units_average_7days_previous_year_diff = units_average_7days - units_average_previous_year
    units_average_30days_previous_year_diff = units_average_30days - units_average_previous_year
    units_average_2days_previous_year_diff = units_average_2days - units_average_previous_year
    units_average_current_year_previous_year_diff = units_average_current_year - units_average_previous_year
    units_today_last_year_previous_year_diff = units_today_last_year - units_average_previous_year

    units_today_30days_diff = units_today - units_average_30days
    units_yesterday_30days_diff = units_yesterday - units_average_30days
    units_average_30days_diff = units_average - units_average_30days
    units_average_7days_30days_diff = units_average_7days - units_average_30days
    units_average_2days_30days_diff = units_average_2days - units_average_30days
    units_average_current_year_30days_diff = units_average_current_year - units_average_30days
    units_average_previous_year_30days_diff = units_average_previous_year - units_average_30days
    units_today_last_year_30days_diff = units_today_last_year - units_average_30days

    placeholder['units_today'] = units_today
    placeholder['units_today_last_year'] = units_today_last_year
    placeholder['units_yesterday'] = units_yesterday
    placeholder['units_average'] = "{:.2f}".format(units_average)
    placeholder['units_average_30days'] = units_average_30days
    placeholder['units_average_previous_year'] = "{:.2f}".format(units_average_previous_year)
    placeholder['units_average_7days'] = units_average_7days
    placeholder['units_average_2days'] = units_average_2days
    placeholder['now'] = time.ctime()
    placeholder['moves_csv_modified'] = time.ctime(os.path.getmtime(MOVES_CSV_FILENAME))
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

    with open(TEMPLATE_FILENAME, "r") as myfile:
        template = myfile.read()

    formated = template.format(**placeholder)
    print formated
