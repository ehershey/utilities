#!/usr/bin/env python
# Update moves summary collection with values from Moves App
#
# Requires $MOVES_ACCESS_TOKEN environment variable
#

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

#
if "MOVES_ACCESS_TOKEN" not in os.environ:
    raise Exception("No $MOVES_ACCESS_TOKEN defined.")
if "MONGODB_URI" not in os.environ:
    raise Exception("No $MONGODB_URI defined.")
MOVES_ACCESS_TOKEN = os.environ["MOVES_ACCESS_TOKEN"]
MONGODB_URI = os.environ["MONGODB_URI"]

url = "https://api.moves-app.com/api/1.1/user/summary/daily?pastDays=10&access_token={token}".format(token=MOVES_ACCESS_TOKEN)

# print("url: {url}".format(url=url))


# client = MongoClient()
client = MongoClient(MONGODB_URI)

db = client[DB]

collection = db[COLLECTION]

r = requests.get(url)
if r.status_code != 200:
    raise Exception("Bad status code: {code}".format(r.status_Code))
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
                calories += activity_calories
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
            record[verbose_activity_name_duration] = ("%.2f" % duration_seconds)
            # sys.stdout.write("%.2f" % duration_seconds)

    record['Calories'] = ("%d" % calories)
    # print(record)
    # sys.stdout.write(",%d" % calories)
    # sys.stdout.write("\n")
    filter = {"Date": record['Date']}
    result = collection.replace_one(filter, record, upsert=True)
    # print("result: ")
    # print(result)


#
