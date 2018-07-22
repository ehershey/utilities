#!/usr/bin/env python
"""
Watch for tcx files saved by Tapiriik.
When they come in, do some analysis and email results to myself.
"""

from __future__ import print_function
import argparse
import logging
import os
import erniemail
import erniegps
from pymongo import MongoClient


ACTIVITY_DIR = "{0}/Dropbox/Apps/tapiriik".format(os.environ['HOME'])
DB_URL = 'mongodb://localhost:27017/'

DB_NAME = 'ernie_org'
COLLECTION_NAME = 'stat_activities'

RECIPIENT = 'activity-stats@ernie.org'

SENDER = RECIPIENT

# re-process activities without this version #
ACTIVITY_VERSION = 1


def getargs():
    """ Parse command line args """
    parser = argparse.ArgumentParser(
        description='Process Tapiriik activities and send stats emails')
    parser.add_argument(
        '--filter',
        required=False,
        help='Case insensitive regex to limit processed filenames',
        type=str)
    parser.add_argument(
        '--redo',
        default=False,
        help='Process activity whether in DB already or not',
        action='store_true')
    parser.add_argument(
        '--debug',
        default=False,
        help='Print debugging info to stderr',
        action='store_true')
    parser.add_argument(
        '--skip-mail',
        default=False,
        help='Skip sending email, just print track info',
        action='store_true')
    args = parser.parse_args()
    return args


def print_summary(activity):
    """ Output simple activity summary """

    print("is_negative_split: {0}".format(activity['is_negative_split']))
    print("negative_split_depth: {0}".format(activity[
        'negative_split_depth']))
    print(u"notes: {0}".format(activity['notes']))
    print("activity_type: {0}".format(activity['activity_type']))
    print("verbose_starttime: {0}".format(activity['verbose_starttime']))
    print("verbose_startdate: {0}".format(activity['verbose_startdate']))
    print("verbose_duration: {0}".format(activity['verbose_duration']))
    print("verbose_distance: {0}".format(activity['verbose_distance']))


def main():
    """
    Read arguments, do analysis
    """

    args = getargs()

    if args.debug:
        logging.getLogger().setLevel(getattr(logging, "DEBUG"))

    client = MongoClient(DB_URL)

    database = client[DB_NAME]

    collection = database[COLLECTION_NAME]

    collection.create_index("filename", unique=True)

    created_count = 0

    for basename in os.listdir(ACTIVITY_DIR):
        filename = os.path.join(ACTIVITY_DIR, basename)
        if "tcx" in filename and (args.filter is None or args.filter.lower() in filename.lower()):
            logging.debug("Processing filename: %s", filename)

            activity_query = {"filename": filename}
            activity = collection.find_one(activity_query)
            create_activity = False
            create_activity_reason = None
            logging.debug("activity: %s", activity)
            if activity is None:
                create_activity = True
                create_activity_reason = "No activity in DB"
            elif 'activity_version' not in activity:
                create_activity = True
                create_activity_reason = "No version in DB"
            elif activity['activity_version'] < ACTIVITY_VERSION:
                create_activity = True
                create_activity_reason = "Version in DB too low ({0} < {1})".format(
                    activity['activity_version'], ACTIVITY_VERSION)
            elif args.redo:
                create_activity = True
                create_activity_reason = "Redo flag passed"

            if create_activity:
                logging.debug("Reading filename: %s", filename)
                activity = erniegps.read_activity(filename)
                logging.debug("Processing activity: %s", activity)
                activity = erniegps.process_activity(activity)

                activity['activity_version'] = ACTIVITY_VERSION

                logging.debug("Created activity ( %s )", create_activity_reason)

                result = collection.replace_one(
                    activity_query, activity, upsert=True)
                upserted_id = result.upserted_id
                logging.debug("upserted_id: %s", upserted_id)
                created_count += 1

                print_summary(activity)

                if not args.skip_mail:
                    erniemail.activity_notify(activity, RECIPIENT, SENDER)
            else:
                logging.debug("Found pre-existing activity in db")

        else:
            logging.debug("Skipping filename: %s", filename)
    print("created_count: {0}".format(created_count))


if __name__ == '__main__':
    main()
