#!/usr/bin/env python
"""

Watch for tcx files saved by Tapiriik.
When they come in, do some analysis and email results to myself.
"""

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


def main():
    """
    Parse arguments, do analysis
    """
    parser = argparse.ArgumentParser(description='Process Tapiriik activities and send stats emails')
    parser.add_argument('--filter', required=False, help='Case insensitive regex to limit processed filenames', type=str)
    parser.add_argument('--redo', default=False, help='Process activity whether in DB already or not', action='store_true')
    args = parser.parse_args()

    client = MongoClient(DB_URL)

    db = MongoClient(DB_URL)[DB_NAME]

    collection = db[COLLECTION_NAME]

    collection.create_index("filename", unique=True)

    created_count = 0

    for basename in os.listdir(ACTIVITY_DIR):
        filename = os.path.join(ACTIVITY_DIR, basename)
        if "tcx" in filename and (args.filter is None or args.filter.lower() in filename.lower()):
            logging.debug("Processing filename: {0}".format(filename))

            activity_query = {"filename": filename}
            activity = collection.find_one(activity_query)
            create_activity = False
            create_activity_reason = None
            if activity is None:
                create_activity = True
                create_activity_reason = "No activity in DB"
            elif 'activity_version' not in activity:
                create_activity = True
                create_activity_reason = "No version in DB"
            elif activity['activity_version'] < ACTIVITY_VERSION:
                create_activity = True
                create_activity_reason = "Version in DB too low ({0} < {0})".format(
                    activity['activity_version'], ACTIVITY_VERSION)
            elif args.redo:
                create_activity = True
                create_activity_reason = "Redo flag passed"

            if create_activity:
                print("reading filename: {0}".format(filename))
                activity = erniegps.read_activity(filename)
                activity = erniegps.process_activity(activity)

                activity['activity_version'] = ACTIVITY_VERSION

                print("Created activity ( {0} )".format(create_activity_reason))

                result = collection.replace_one(
                    activity_query, activity, upsert=True)
                upserted_id = result.upserted_id
                logging.debug("upserted_id: {0}".format(upserted_id))
                created_count += 1

                # exit()

                print("is_negative_split: {0}".format(activity['is_negative_split']))
                print("negative_split_depth: {0}".format(activity[
                    'negative_split_depth']))
                print(u"notes: {0}".format(activity['notes']))
                print("activity_type: {0}".format(activity['activity_type']))
                print("verbose_starttime: {0}".format(activity['verbose_starttime']))
                print("verbose_startdate: {0}".format(activity['verbose_startdate']))
                print("verbose_duration: {0}".format(activity['verbose_duration']))
                print("verbose_distance: {0}".format(activity['verbose_distance']))

                erniemail.activity_notify(activity, RECIPIENT, SENDER)
            else:
                logging.debug("Found activity")

        else:
            logging.debug("Skipping filename: {0}".format(filename))
    print("created_count: {0}".format(created_count))


if __name__ == '__main__':
    main()
