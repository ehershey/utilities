#!/usr/bin/env python
#
# Email when daily calorie expenditure passes various thresholds:
# Half of any of the averages below
# Seven day average
# Thirty day average
# This year average
# Overall average
# Double overall average
#

import erniemail
import sys
import unit_report
from pymongo import MongoClient
from os.path import expanduser
import os

COLLECTION = "daily_summary"
DB = "ernie_org"

sender = "average_calorie_checker@eahdroplet4.ernie.org"
recipient = "average_calorie_checker@ernie.org"
subject = ""

home = expanduser("~ernie")

if "MONGODB_URI" not in os.environ:
    raise Exception("No $MONGODB_URI defined.")
MONGODB_URI = os.environ["MONGODB_URI"]

client = MongoClient(MONGODB_URI)

db = client[DB]

collection = db[COLLECTION]

calories_average = unit_report.get_units_average(collection)

sys.stderr.write("calories_average from db: {0}\n".format(calories_average))

calories_today = unit_report.get_units_today(collection)

sys.stderr.write("calories_today from db: {0}\n".format(calories_today))

calories_7days = unit_report.get_7day_average(collection)

sys.stderr.write("calories_7days from db: {0}\n".format(calories_7days))

calories_30days = unit_report.get_30day_average(collection)

sys.stderr.write("calories_30days from db: {0}\n".format(calories_30days))

calories_average_current_year = unit_report.get_units_average_current_year(
        collection)

sys.stderr.write("calories_average_current_year from db: {0}\n".format(
    calories_average_current_year))


LOCKFILE = "/tmp/mailed_calorie_message.lock"
LOCKFILE_DOUBLE = "/tmp/mailed_double_calorie_message.lock"
LOCKFILE_HALF = "/tmp/mailed_half_calorie_message.lock"
LOCKFILE_7DAYS = "/tmp/mailed_7days_calorie_message.lock"
LOCKFILE_30DAYS = "/tmp/mailed_30days_calorie_message.lock"
LOCKFILE_YEAR = "/tmp/mailed_year_calorie_message.lock"

if calories_today > calories_average:
    if not os.path.exists(LOCKFILE):
        sys.stderr.write("emailing about overall average\n")
        body_raw = "Surpassed overall calorie average! (today: {0}, average: {1})"
        body = body_raw.format(calories_today, calories_average)
        erniemail.send_message(body, subject, recipient, sender)
        with open(LOCKFILE, 'a'):
            os.utime(LOCKFILE, None)
else:
    if os.path.exists(LOCKFILE):
        sys.stderr.write("resetting lockfile for overall average\n")
        os.unlink(LOCKFILE)

if calories_today > calories_average * 2:
    if not os.path.exists(LOCKFILE_DOUBLE):
        sys.stderr.write("emailing about double average\n")
        body_raw = "Surpassed DOUBLE calorie average! (today: {0}, double average: {1})"
        body = body_raw.format(calories_today, calories_average * 2)
        erniemail.send_message(body, subject, recipient, sender)
        with open(LOCKFILE_DOUBLE, 'a'):
            os.utime(LOCKFILE_DOUBLE, None)
else:
    if os.path.exists(LOCKFILE_DOUBLE):
        sys.stderr.write("resetting lockfile for double average\n")
        os.unlink(LOCKFILE_DOUBLE)

# this logic doesn't make sense
# TODO - fix it
half_body = None
if calories_today > calories_average / 2:
    body_raw = "Surpassed HALF of overall calorie average! (today: {0}, half average: {1})"
    half_body = body_raw.format(calories_today, calories_average / 2)
elif calories_today > calories_7days / 2:
    body_raw = "Surpassed HALF of 7 day calorie average! (today: {0}, half average: {1})"
    half_body = body_raw.format(calories_today, calories_7days / 2)
elif calories_today > calories_30days / 2:
    body_raw = "Surpassed HALF of 30 day calorie average! (today: {0}, half average: {1})"
    half_body = body_raw.format(calories_today, calories_30days / 2)
elif calories_today > calories_average_current_year / 2:
    body_raw = "Surpassed HALF of current year calorie average! (today: {0}, half average: {1})"
    half_body = body_raw.format(calories_today, calories_average_current_year / 2)
if half_body is not None:
    if not os.path.exists(LOCKFILE_HALF):
        sys.stderr.write("emailing about half average\n")
        erniemail.send_message(half_body, subject, recipient, sender)
        with open(LOCKFILE_HALF, 'a'):
            os.utime(LOCKFILE_HALF, None)
else:
    if os.path.exists(LOCKFILE_HALF):
        sys.stderr.write("resetting lockfile for half average\n")
        os.unlink(LOCKFILE_HALF)


if calories_today > calories_7days:
    if not os.path.exists(LOCKFILE_7DAYS):
        sys.stderr.write("emailing about 7 day average\n")
        body_raw = "Surpassed 7 day calorie average! (today: {0}, 7 day average: {1})"
        body = body_raw.format(calories_today, calories_7days)
        erniemail.send_message(body, subject, recipient, sender)
        with open(LOCKFILE_7DAYS, 'a'):
            os.utime(LOCKFILE_7DAYS, None)
else:
    if os.path.exists(LOCKFILE_7DAYS):
        sys.stderr.write("resetting lockfile for 7 day average\n")
        os.unlink(LOCKFILE_7DAYS)

if calories_today > calories_30days:
    if not os.path.exists(LOCKFILE_30DAYS):
        sys.stderr.write("emailing about 30 day average\n")
        body_raw = "Surpassed 30 day calorie average! (today: {0}, 30 day average: {1})"
        body = body_raw.format(calories_today, calories_30days)
        erniemail.send_message(body, subject, recipient, sender)
        with open(LOCKFILE_30DAYS, 'a'):
            os.utime(LOCKFILE_30DAYS, None)
else:
    if os.path.exists(LOCKFILE_30DAYS):
        sys.stderr.write("resetting lockfile for 30 day average\n")
        os.unlink(LOCKFILE_30DAYS)
