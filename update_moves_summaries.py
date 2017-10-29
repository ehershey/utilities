#!/usr/bin/env python
# Update moves summary collection with values from Moves App
#
# Requires $MOVES_ACCESS_TOKEN and MONGODB_URI environment variables
#

import argparse
import datetime
import os
from pymongo import MongoClient
import requests
import simplejson as json
import re
import sys
import subprocess
import time

COLLECTION = "summaries"
DB = "moves"


parser = argparse.ArgumentParser(description='Update Database from Moves API')
parser.add_argument('--redo', action='store_true', required=False, help='Load old data', default = False);
parser.add_argument('--month', required=False, help='Month for which to load old data (format: NN)', type=int);
parser.add_argument('--year', required=False, help='Year for which to load old data (format: NN)', type=int);
args = parser.parse_args()

redo = args.redo
month = args.month
year = args.year

#
if "MOVES_ACCESS_TOKEN" not in os.environ:
    raise Exception("No $MOVES_ACCESS_TOKEN defined.")
if "MONGODB_URI" not in os.environ:
    raise Exception("No $MONGODB_URI defined.")
MOVES_ACCESS_TOKEN = os.environ["MOVES_ACCESS_TOKEN"]
MONGODB_URI = os.environ["MONGODB_URI"]

# client = MongoClient()
client = MongoClient(MONGODB_URI)

db = client[DB]

collection = db[COLLECTION]


def process_month(year, month):
    url = "https://api.moves-app.com/api/1.1/user/summary/daily/{year}{month:02d}?access_token={token}".format(token=MOVES_ACCESS_TOKEN, month = month, year = year)
    try:
       process_url(url)
    except Exception as error:
        print("Error: {error}".format(error=error))


def process_url(url):
    print("url: {url}".format(url=url))

    r = requests.get(url)
    if r.status_code != 200:
        print("Bad status code")
        print("r.text: {text}".format(text = r.text))
        raise Exception("Bad status code: {code}".format(code = r.status_code))
    # print( r.json())

    response = r.json()

    METERS_IN_ONE_MILE = 1609.34

    verbose_activity_names = {
        "wlk": "Walking",
        "run": "Running",
        "cyc": "Cycling",
        "walking": "Walking",
        "running": "Running",
        "cycling": "Cycling",
        "swimming": "Swimming",
        "car": "Car",
        "transport": "Transport",
        "airplane": "Airplane"
    }

    UNKNOWN_ACTIVITY_BUCKET_VERBOSE_NAME = "Unknown"

    verbose_activity_name_list = list(set(sorted(verbose_activity_names.values())))

    verbose_activity_name_list.append(UNKNOWN_ACTIVITY_BUCKET_VERBOSE_NAME)


    if hasattr(datetime.datetime, 'strptime'):
        # python 2.6
        strptime = datetime.datetime.strptime
    else:
        # python 2.4 equivalent
        def strptime(date_string, format):
            return datetime.datetime(*(time.strptime(date_string, format)[0:6]))

        # output = json.load(instream)

    for index, summary in enumerate(response):
        record = {}
        activities = summary['summary']
        # sys.stdout.write(str(strptime(summary['date'], '%Y%m%d')))
        record['Date'] = strptime(summary['date'], '%Y%m%d')
        activities_by_verbose_name = {}
        calories = 0
        if activities:
            for activity in activities:
                verbose_activity_name = verbose_activity_names.get(activity[
                                                                   'activity'])
                if not verbose_activity_name:
                    verbose_activity_name = UNKNOWN_ACTIVITY_BUCKET_VERBOSE_NAME
                activities_by_verbose_name[verbose_activity_name] = activity
                activity_calories = activity.get('calories')
                if activity_calories:
                    calories += float(activity_calories)
        for verbose_activity_name in verbose_activity_name_list:
            if verbose_activity_name in activities_by_verbose_name:
                distance_meters = activities_by_verbose_name[
                    verbose_activity_name].get('distance')
                if distance_meters:
                    distance_miles = distance_meters / METERS_IN_ONE_MILE
                else:
                    distance_miles = 0
                record[verbose_activity_name] = ("%.2fmi" % distance_miles)
                # sys.stdout.write("%.2fmi" % distance_miles)
            if verbose_activity_name in activities_by_verbose_name:
                verbose_activity_name_duration = verbose_activity_name + ' Seconds'
                duration_seconds = activities_by_verbose_name[
                    verbose_activity_name].get('duration')
                record[verbose_activity_name_duration] = float(("%.2f" % duration_seconds))
                # sys.stdout.write("%.2f" % duration_seconds)

        record['Calories'] = float(calories)
        # print(record)
        # sys.stdout.write(",%d" % calories)
        # sys.stdout.write("\n")
        filter = {"Date": record['Date']}
        result = collection.replace_one(filter, record, upsert=True)
        # print("result: ")
        # print(result)


if redo:
    if year:
        if month:
            process_month(year, month)
        else:
            for month in range(1,13):
                process_month(year, month)
    else:
        if month:
            for year in range(2013,datetime.datetime.now().year+1):
                process_month(year, month)
        else:
            for year in range(2013,datetime.datetime.now().year+1):
                for month in range(1,13):
                    process_month(year, month)
else:
    url = "https://api.moves-app.com/api/1.1/user/summary/daily?pastDays=10&access_token={token}".format(token=MOVES_ACCESS_TOKEN)
    process_url(url)

