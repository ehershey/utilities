#!/usr/bin/env python2.7
"""
Output calorie report based on location/motion data in database
Requires MONGODB_URI environment variable
"""
import argparse
import datetime
from datetime import timedelta
import logging
from os.path import expanduser
import os
import os.path
import time
import dateutil.parser
from pymongo import MongoClient


COLLECTION = "daily_summary"
DB = "ernie_org"


def log(function):
    """ convert function into one with debug logging of invocations and return values """
    def decorator(*args, **kwargs):
        logging.debug("{function}(..) start", function=function.__name__)
        value = function(*args, **kwargs)
        logging.debug("{function}(..) returning: {returnvalue}", function=function.__name__,
                      returnvalue=value)
        return value
    return decorator


PARSER = argparse.ArgumentParser(description='Generate calorie report')
PARSER.add_argument('--for-date', help='Date to generate report for', required=False)
PARSER.add_argument(
    '--debug',
    default=False,
    help='Print debugging info to stderr',
    action='store_true')

HOME = expanduser("~ernie")

TEMPLATE_FILENAME = "%s/unit-report-template.html" % os.path.dirname(
    os.path.realpath(__file__))
ARC_GPX_DIR = "%s/Dropbox/Misc/Arc Export" % HOME

PLACEHOLDER = {}

if "MONGODB_URI" not in os.environ:
    raise Exception("No $MONGODB_URI defined.")
MONGODB_URI = os.environ["MONGODB_URI"]


@log
def get_units_average(
        collection,
        forever_ago=datetime.datetime.now() - timedelta(days=50 * 365),
        today=datetime.datetime.now()):
    """ return the average number of calories bruned between two timestamps """

    return int(get_average_between_two_dates(collection, forever_ago, today))


@log
def get_average_between_two_dates(collection, min_date, max_date):
    """ return the average nuber of calories burned between two dates """

    match = {"$match": {"$and": [{"Date": {"$lte": max_date}}, {"Date": {"$gt": min_date}}]}}
    group = {"$group": {"_id": None, "average": {"$avg": "$Calories"}}}

    pipeline = [match, group]

    logging.debug("pipeline: ")
    logging.debug(pipeline)
    cursor = collection.aggregate(pipeline)

    try:
        result = cursor.next()
        average = result['average']
    except StopIteration:
        average = 0
    return average


@log
def get_7day_average(collection, today=datetime.datetime.now()):
    """ 7 day calorie average """
    return int(get_average_between_two_dates(collection, today - timedelta(days=7), today))


@log
def get_2day_average(collection, today=datetime.datetime.now()):
    """ 2 day calorie average """
    return int(get_average_between_two_dates(collection, today - timedelta(days=2), today))


@log
def get_30day_average(collection, today=datetime.datetime.now()):
    """ 30 day calorie average """
    return int(get_average_between_two_dates(collection, today - timedelta(days=30), today))


@log
def get_units_today(collection, day_before_today=datetime.datetime.now() - timedelta(days=1),
                    today=datetime.datetime.now()):
    """ today calorie total """
    return int(get_average_between_two_dates(collection, day_before_today, today))


@log
def get_units_average_current_year(collection, today=datetime.datetime.now()):
    """ current year calorie average """
    last_day_of_previous_year = get_last_day_of_previous_year(today=today)
    last_day_of_current_year = get_last_day_of_current_year(today=today)
    units_average_current_year = int(get_average_between_two_dates(collection,
                                     last_day_of_previous_year,
                                     last_day_of_current_year))
    return units_average_current_year


@log
def get_last_day_of_previous_year(today=datetime.datetime.now()):
    """ get datetime.datetime representing the last calendar day in the previous year from
        today' """
    # use last day of last year to account for db dates being 00:00, so anything > last day of
    # last year will only include this year

    last_day_of_previous_year = today.replace(month=1, day=1) - timedelta(days=1)
    return last_day_of_previous_year


@log
def get_last_day_of_current_year(today=datetime.datetime.now()):
    last_day_of_current_year = today.replace(month=12, day=31)
    return last_day_of_current_year


if __name__ == '__main__':

    client = MongoClient(MONGODB_URI)

    db = client[DB]

    summary_collection = db[COLLECTION]

    ARGS = PARSER.parse_args()
    if ARGS.for_date:
        for_date = dateutil.PARSER.parse(ARGS.for_date).replace(hour=12)
    else:
        for_date = datetime.datetime.now()

    if ARGS.debug:
        logging.getLogger().setLevel(getattr(logging, "DEBUG"))

    yesterday = for_date - timedelta(days=1)
    day_before_yesterday = yesterday - timedelta(days=1)

    current_year = for_date.year
    previous_year = current_year - 1

    current_month = for_date.month
    previous_month = current_month - 1

    current_day = for_date.day
    previous_day = current_day - 1

    today_last_year = for_date.replace(year=previous_year)
    yesterday_last_year = today_last_year - timedelta(days=1)

    units_today = get_units_today(summary_collection, yesterday, for_date)

    units_average = get_units_average(summary_collection)

    units_yesterday = int(get_average_between_two_dates(summary_collection, day_before_yesterday,
                          yesterday))

    units_today_last_year = int(get_average_between_two_dates(summary_collection,
                                yesterday_last_year, today_last_year))

    # use last day of two years ago to account for db dates being 00:00, so anything > last day of
    # two years ago will only include last year, not two years ago

    last_day_of_year_before_previous_year = today_last_year.replace(month=1, day=1) -\
        timedelta(days=1)

    last_day_of_previous_year = get_last_day_of_previous_year(today=for_date)

    units_average_previous_year = int(get_average_between_two_dates(summary_collection,
                                      last_day_of_year_before_previous_year,
                                      last_day_of_previous_year))

    units_average_current_year = get_units_average_current_year(summary_collection, today=for_date)

    units_average_7days = get_7day_average(summary_collection, for_date)
    units_average_2days = get_2day_average(summary_collection, for_date)
    units_average_30days = get_30day_average(summary_collection, for_date)
    units_today_previous_year_diff = units_today - units_average_previous_year
    units_yesterday_previous_year_diff = units_yesterday - units_average_previous_year
    units_average_previous_year_diff = units_average - units_average_previous_year
    units_average_7days_previous_year_diff = units_average_7days - units_average_previous_year
    units_average_30days_previous_year_diff = units_average_30days - units_average_previous_year
    units_average_2days_previous_year_diff = units_average_2days - units_average_previous_year
    units_average_current_year_previous_year_diff = units_average_current_year -\
        units_average_previous_year
    units_today_last_year_previous_year_diff = units_today_last_year - units_average_previous_year

    units_today_30days_diff = units_today - units_average_30days
    units_yesterday_30days_diff = units_yesterday - units_average_30days
    units_average_30days_diff = units_average - units_average_30days
    units_average_7days_30days_diff = units_average_7days - units_average_30days
    units_average_2days_30days_diff = units_average_2days - units_average_30days
    units_average_current_year_30days_diff = units_average_current_year - units_average_30days
    units_average_previous_year_30days_diff = units_average_previous_year - units_average_30days
    units_today_last_year_30days_diff = units_today_last_year - units_average_30days

    PLACEHOLDER['units_today'] = units_today
    PLACEHOLDER['units_today_last_year'] = units_today_last_year
    PLACEHOLDER['units_yesterday'] = units_yesterday
    PLACEHOLDER['units_average'] = "{:.2f}".format(units_average)
    PLACEHOLDER['units_average_30days'] = units_average_30days
    PLACEHOLDER['units_average_previous_year'] = "{:.2f}".format(units_average_previous_year)
    PLACEHOLDER['units_average_7days'] = units_average_7days
    PLACEHOLDER['units_average_2days'] = units_average_2days
    PLACEHOLDER['now'] = time.ctime()
    PLACEHOLDER['moves_csv_modified'] = time.ctime(os.path.getmtime(ARC_GPX_DIR))
    PLACEHOLDER['units_average_current_year'] = units_average_current_year

    PLACEHOLDER['units_today_previous_year_diff'] = units_today_previous_year_diff
    PLACEHOLDER['units_today_last_year_previous_year_diff'] = \
        units_today_last_year_previous_year_diff
    PLACEHOLDER['units_yesterday_previous_year_diff'] = units_yesterday_previous_year_diff
    PLACEHOLDER['units_average_previous_year_diff'] = units_average_previous_year_diff
    PLACEHOLDER['units_average_7days_previous_year_diff'] = units_average_7days_previous_year_diff
    PLACEHOLDER['units_average_30days_previous_year_diff'] = units_average_30days_previous_year_diff
    PLACEHOLDER['units_average_2days_previous_year_diff'] = units_average_2days_previous_year_diff
    PLACEHOLDER['units_average_current_year_previous_year_diff'] = \
        units_average_current_year_previous_year_diff

    PLACEHOLDER['units_today_30days_diff'] = units_today_30days_diff
    PLACEHOLDER['units_today_last_year_30days_diff'] = units_today_last_year_30days_diff
    PLACEHOLDER['units_yesterday_30days_diff'] = units_yesterday_30days_diff
    PLACEHOLDER['units_average_30days_diff'] = units_average_30days_diff
    PLACEHOLDER['units_average_7days_30days_diff'] = units_average_7days_30days_diff
    PLACEHOLDER['units_average_2days_30days_diff'] = units_average_2days_30days_diff
    PLACEHOLDER['units_average_current_year_30days_diff'] = units_average_current_year_30days_diff
    PLACEHOLDER['units_average_previous_year_30days_diff'] = units_average_previous_year_30days_diff

    PLACEHOLDER['current_year'] = current_year
    PLACEHOLDER['previous_year'] = previous_year
    PLACEHOLDER['today_class'] = ""
    PLACEHOLDER['2days_class'] = ""
    PLACEHOLDER['7days_class'] = ""
    PLACEHOLDER['alltime_class'] = ""

    with open(TEMPLATE_FILENAME, "r") as myfile:
        template = myfile.read()

    formated = template.format(**PLACEHOLDER)
    print(formated)
