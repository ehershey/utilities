#!/usr/bin/env python3
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
from pymongo import DESCENDING


COLLECTION = "daily_summary"
DB = "ernie_org"


def log(function):
    """ convert function into one with debug logging of invocations and return values """
    def decorator(*args, **kwargs):
        logging.debug("{function}(..) start".format(function=function.__name__))
        value = function(*args, **kwargs)
        logging.debug("{function}(..) returning: {returnvalue}".format(
            function=function.__name__, returnvalue=value))
        return value
    return decorator


@log
def get_last_data_timestamp(collection):
    try:
        most_recent_summary = collection.find().sort('_id', DESCENDING).limit(1).next()
        id = most_recent_summary['_id']
        gentime = id.generation_time
    except StopIteration:
        gentime = datetime.datetime.fromtimestamp(0)
    return gentime


PARSER = argparse.ArgumentParser(description='Generate calorie report')
PARSER.add_argument('--run-timestamp', help='Explicit execution timestamp for template',
                    required=False)
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
        older_date=datetime.datetime.now() - timedelta(days=50 * 365),
        today=datetime.datetime.now(), activity_type=None, entry_source=None):
    """ return the average number of calories burned between two timestamps """

    return int(get_average_between_two_dates(collection, older_date, today,
               activity_type=activity_type, entry_source=entry_source))


@log
def get_average_between_two_dates(collection, min_date, max_date, activity_type,
                                  entry_source):
    """ return the average number of calories burned between two dates """

    if activity_type is not None:
        calories_field = "calories_by_type.{activity_type}".format(activity_type=activity_type)
    elif entry_source is not None:
        calories_field = "calories_by_entry_source.{entry_source}".format(entry_source=entry_source)
    else:
        calories_field = "Calories"

    match = {"$match": {"$and": [{"Date": {"$lte": max_date}},
             {"Date": {"$gt": min_date}}]}}
    group = {"$group": {"_id": None, "average":
             {"$avg": "${calories_field}".format(calories_field=calories_field)}}}

    pipeline = [match, group]

    logging.debug("pipeline: ")
    logging.debug(pipeline)
    cursor = collection.aggregate(pipeline)

    try:
        result = cursor.next()
        average = result['average']
    except StopIteration:
        average = 0
    if average is None:
        average = 0
    return average


@log
def get_7day_average(collection, today=datetime.datetime.now()):
    """ 7 day calorie average """
    return get_units_average(collection, today - timedelta(days=7), today)


@log
def get_2day_average(collection, today=datetime.datetime.now()):
    """ 2 day calorie average """
    return get_units_average(collection, today - timedelta(days=2), today)


@log
def get_30day_average(collection, today=datetime.datetime.now()):
    """ 30 day calorie average """
    return get_units_average(collection, today - timedelta(days=30), today)


@log
def get_units_average_current_year(collection, today=datetime.datetime.now()):
    """ current year calorie average """
    last_day_of_previous_year = get_last_day_of_previous_year(today=today)
    last_day_of_current_year = get_last_day_of_current_year(today=today)
    units_average_current_year = get_units_average(collection,
                                                   last_day_of_previous_year,
                                                   last_day_of_current_year)
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


@log
def get_units_today(collection, today=datetime.datetime.now(),
                    yesterday=datetime.datetime.now() - timedelta(days=1)):
    return get_units_average(collection, today=today, older_date=yesterday)


if __name__ == '__main__':
    client = MongoClient(MONGODB_URI)

    db = client[DB]

    summary_collection = db[COLLECTION]

    ARGS = PARSER.parse_args()
    if ARGS.for_date:
        for_date = dateutil.parser.parse(ARGS.for_date).replace(hour=12)
    else:
        for_date = datetime.datetime.now().replace(hour=12)

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

    try:
        today_last_year = for_date.replace(year=previous_year)
    except ValueError:
        # try yesterday in case of leap day or other weirdness
        today_last_year = yesterday.replace(year=previous_year)

    yesterday_last_year = today_last_year - timedelta(days=1)

    units_today = get_units_average(summary_collection, yesterday, for_date)

    units_average = get_units_average(summary_collection)

    units_yesterday = get_units_average(summary_collection, day_before_yesterday,
                                        yesterday)

    units_today_last_year = get_units_average(summary_collection,
                                              yesterday_last_year, today_last_year)

    last_data_timestamp = get_last_data_timestamp(summary_collection).ctime()

    # use last day of two years ago to account for db dates being 00:00, so anything > last day of
    # two years ago will only include last year, not two years ago

    last_day_of_year_before_previous_year = today_last_year.replace(month=1, day=1) -\
        timedelta(days=1)

    last_day_of_previous_year = get_last_day_of_previous_year(today=for_date)

    units_average_previous_year = get_units_average(summary_collection,
                                                    last_day_of_year_before_previous_year,
                                                    last_day_of_previous_year)

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
    PLACEHOLDER['data_updated'] = last_data_timestamp
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

    # fill in big table at the bottom
    #
    PLACEHOLDER['units_two_days_ago'] = \
        get_units_average(summary_collection, for_date - timedelta(days=3),
                          for_date - timedelta(days=2))
    PLACEHOLDER['units_three_days_ago'] = \
        get_units_average(summary_collection, for_date - timedelta(days=4),
                          for_date - timedelta(days=3))
    PLACEHOLDER['units_four_days_ago'] = \
        get_units_average(summary_collection, for_date - timedelta(days=5),
                          for_date - timedelta(days=4))
    PLACEHOLDER['units_five_days_ago'] = \
        get_units_average(summary_collection, for_date - timedelta(days=6),
                          for_date - timedelta(days=5))
    PLACEHOLDER['units_six_days_ago'] = \
        get_units_average(summary_collection, for_date - timedelta(days=7),
                          for_date - timedelta(days=6))
    PLACEHOLDER['day_of_week_two_days_ago'] = (for_date - timedelta(days=2)).strftime("%A")
    PLACEHOLDER['day_of_week_three_days_ago'] = (for_date - timedelta(days=3)).strftime("%A")
    PLACEHOLDER['day_of_week_four_days_ago'] = (for_date - timedelta(days=4)).strftime("%A")
    PLACEHOLDER['day_of_week_five_days_ago'] = (for_date - timedelta(days=5)).strftime("%A")
    PLACEHOLDER['day_of_week_six_days_ago'] = (for_date - timedelta(days=6)).strftime("%A")

    PLACEHOLDER['date_today'] = for_date.strftime("%Y-%m-%d")
    PLACEHOLDER['date_yesterday'] = (for_date - timedelta(days=1)).strftime("%Y-%m-%d")
    PLACEHOLDER['date_two_days_ago'] = (for_date - timedelta(days=2)).strftime("%Y-%m-%d")
    PLACEHOLDER['date_three_days_ago'] = (for_date - timedelta(days=3)).strftime("%Y-%m-%d")
    PLACEHOLDER['date_four_days_ago'] = (for_date - timedelta(days=4)).strftime("%Y-%m-%d")
    PLACEHOLDER['date_five_days_ago'] = (for_date - timedelta(days=5)).strftime("%Y-%m-%d")
    PLACEHOLDER['date_six_days_ago'] = (for_date - timedelta(days=6)).strftime("%Y-%m-%d")

    PLACEHOLDER['units_today_cycling'] = \
        get_units_average(summary_collection, for_date - timedelta(days=1), for_date,
                          activity_type="Cycling")
    PLACEHOLDER['units_yesterday_cycling'] = \
        get_units_average(summary_collection, for_date - timedelta(days=2),
                          for_date - timedelta(days=1), activity_type="Cycling")
    PLACEHOLDER['units_two_days_ago_cycling'] = \
        get_units_average(summary_collection, for_date - timedelta(days=3),
                          for_date - timedelta(days=2), activity_type="Cycling")
    PLACEHOLDER['units_three_days_ago_cycling'] = \
        get_units_average(summary_collection, for_date - timedelta(days=4),
                          for_date - timedelta(days=3), activity_type="Cycling")
    PLACEHOLDER['units_four_days_ago_cycling'] = \
        get_units_average(summary_collection, for_date - timedelta(days=5),
                          for_date - timedelta(days=4), activity_type="Cycling")
    PLACEHOLDER['units_five_days_ago_cycling'] = \
        get_units_average(summary_collection, for_date - timedelta(days=6),
                          for_date - timedelta(days=5), activity_type="Cycling")
    PLACEHOLDER['units_six_days_ago_cycling'] = \
        get_units_average(summary_collection, for_date - timedelta(days=7),
                          for_date - timedelta(days=6), activity_type="Cycling")

    PLACEHOLDER['units_today_running'] = \
        get_units_average(summary_collection, for_date - timedelta(days=1), for_date,
                          activity_type="Running")
    PLACEHOLDER['units_yesterday_running'] = \
        get_units_average(summary_collection,
                          for_date - timedelta(days=2), for_date - timedelta(days=1),
                          activity_type="Running")
    PLACEHOLDER['units_two_days_ago_running'] = \
        get_units_average(summary_collection,
                          for_date - timedelta(days=3), for_date - timedelta(days=2),
                          activity_type="Running")
    PLACEHOLDER['units_three_days_ago_running'] = \
        get_units_average(summary_collection,
                          for_date - timedelta(days=4), for_date - timedelta(days=3),
                          activity_type="Running")
    PLACEHOLDER['units_four_days_ago_running'] = \
        get_units_average(summary_collection,
                          for_date - timedelta(days=5), for_date - timedelta(days=4),
                          activity_type="Running")
    PLACEHOLDER['units_five_days_ago_running'] = \
        get_units_average(summary_collection,
                          for_date - timedelta(days=6), for_date - timedelta(days=5),
                          activity_type="Running")
    PLACEHOLDER['units_six_days_ago_running'] = \
        get_units_average(summary_collection,
                          for_date - timedelta(days=7), for_date - timedelta(days=6),
                          activity_type="Running")

    PLACEHOLDER['units_today_walking'] = \
        get_units_average(summary_collection,
                          for_date - timedelta(days=1), for_date, activity_type="Walking")
    PLACEHOLDER['units_yesterday_walking'] = \
        get_units_average(summary_collection, for_date - timedelta(days=2),
                          for_date - timedelta(days=1), activity_type="Walking")
    PLACEHOLDER['units_two_days_ago_walking'] = \
        get_units_average(summary_collection, for_date - timedelta(days=3),
                          for_date - timedelta(days=2), activity_type="Walking")
    PLACEHOLDER['units_three_days_ago_walking'] = \
        get_units_average(summary_collection, for_date - timedelta(days=4),
                          for_date - timedelta(days=3), activity_type="Walking")
    PLACEHOLDER['units_four_days_ago_walking'] = \
        get_units_average(summary_collection, for_date - timedelta(days=5),
                          for_date - timedelta(days=4), activity_type="Walking")
    PLACEHOLDER['units_five_days_ago_walking'] = \
        get_units_average(summary_collection, for_date - timedelta(days=6),
                          for_date - timedelta(days=5), activity_type="Walking")
    PLACEHOLDER['units_six_days_ago_walking'] = \
        get_units_average(summary_collection, for_date - timedelta(days=7),
                          for_date - timedelta(days=6), activity_type="Walking")

    PLACEHOLDER['units_today_strava'] = \
        get_units_average(summary_collection, for_date - timedelta(days=1), for_date,
                          entry_source="Strava")
    PLACEHOLDER['units_yesterday_strava'] = \
        get_units_average(summary_collection, for_date - timedelta(days=2),
                          for_date - timedelta(days=1), entry_source="Strava")
    PLACEHOLDER['units_two_days_ago_strava'] = \
        get_units_average(summary_collection, for_date - timedelta(days=3),
                          for_date - timedelta(days=2), entry_source="Strava")
    PLACEHOLDER['units_three_days_ago_strava'] = \
        get_units_average(summary_collection, for_date - timedelta(days=4),
                          for_date - timedelta(days=3), entry_source="Strava")
    PLACEHOLDER['units_four_days_ago_strava'] = \
        get_units_average(summary_collection, for_date - timedelta(days=5),
                          for_date - timedelta(days=4), entry_source="Strava")
    PLACEHOLDER['units_five_days_ago_strava'] = \
        get_units_average(summary_collection, for_date - timedelta(days=6),
                          for_date - timedelta(days=5), entry_source="Strava")
    PLACEHOLDER['units_six_days_ago_strava'] = \
        get_units_average(summary_collection, for_date - timedelta(days=7),
                          for_date - timedelta(days=6), entry_source="Strava")

    PLACEHOLDER['units_today_livetrack'] = \
        get_units_average(summary_collection, for_date - timedelta(days=1), for_date,
                          entry_source="Livetrack")
    PLACEHOLDER['units_yesterday_livetrack'] = \
        get_units_average(summary_collection, for_date - timedelta(days=2),
                          for_date - timedelta(days=1), entry_source="Livetrack")
    PLACEHOLDER['units_two_days_ago_livetrack'] = \
        get_units_average(summary_collection, for_date - timedelta(days=3),
                          for_date - timedelta(days=2), entry_source="Livetrack")
    PLACEHOLDER['units_three_days_ago_livetrack'] = \
        get_units_average(summary_collection, for_date - timedelta(days=4),
                          for_date - timedelta(days=3), entry_source="Livetrack")
    PLACEHOLDER['units_four_days_ago_livetrack'] = \
        get_units_average(summary_collection, for_date - timedelta(days=5),
                          for_date - timedelta(days=4), entry_source="Livetrack")
    PLACEHOLDER['units_five_days_ago_livetrack'] = \
        get_units_average(summary_collection, for_date - timedelta(days=6),
                          for_date - timedelta(days=5), entry_source="Livetrack")
    PLACEHOLDER['units_six_days_ago_livetrack'] = \
        get_units_average(summary_collection, for_date - timedelta(days=7),
                          for_date - timedelta(days=6), entry_source="Livetrack")

    PLACEHOLDER['units_today_arc'] = \
        get_units_average(summary_collection, for_date - timedelta(days=1), for_date,
                          entry_source="Arc GPX")
    PLACEHOLDER['units_yesterday_arc'] = \
        get_units_average(summary_collection, for_date - timedelta(days=2),
                          for_date - timedelta(days=1), entry_source="Arc GPX")
    PLACEHOLDER['units_two_days_ago_arc'] = \
        get_units_average(summary_collection, for_date - timedelta(days=3),
                          for_date - timedelta(days=2), entry_source="Arc GPX")
    PLACEHOLDER['units_three_days_ago_arc'] = \
        get_units_average(summary_collection, for_date - timedelta(days=4),
                          for_date - timedelta(days=3), entry_source="Arc GPX")
    PLACEHOLDER['units_four_days_ago_arc'] = \
        get_units_average(summary_collection, for_date - timedelta(days=5),
                          for_date - timedelta(days=4), entry_source="Arc GPX")
    PLACEHOLDER['units_five_days_ago_arc'] = \
        get_units_average(summary_collection, for_date - timedelta(days=6),
                          for_date - timedelta(days=5), entry_source="Arc GPX")
    PLACEHOLDER['units_six_days_ago_arc'] = \
        get_units_average(summary_collection, for_date - timedelta(days=7),
                          for_date - timedelta(days=6), entry_source="Arc GPX")

    with open(TEMPLATE_FILENAME, "r") as myfile:
        template = myfile.read()

    formated = template.format(**PLACEHOLDER)
    print(formated)
