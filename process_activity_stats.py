#!/usr/bin/env python
#
#
# Watch for tcx files saved by Tapiriik.
# When they come in, do some analysis and
# email results to myself.

import argparse
import erniemail
import erniegps
import logging
import os
import pymongo
from pymongo import MongoClient

activity_dir = "{0}/Dropbox/Apps/tapiriik".format(os.environ['HOME'])
db_url = 'mongodb://localhost:27017/'

db_name = 'ernie_org'
collection_name = 'stat_activities'

recipient = 'activity-stats@ernie.org'

sender = recipient

# re-process activities without this version #
ACTIVITY_VERSION = 1

parser = argparse.ArgumentParser(description='Process Tapiriik activities and send stats emails')
parser.add_argument('--filter', required=False, help='Case insensitive regex to limit processed filenames', type=str)
args = parser.parse_args()

client = MongoClient(db_url)

db = client[db_name]

collection = db[collection_name]

collection.create_index("filename", unique=True)

created_count = 0

for basename in os.listdir(activity_dir):
    filename = os.path.join(activity_dir, basename)
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

        if create_activity:
            print("reading filename: {0}".format(filename))
            activity = erniegps.read_activity(filename)
            activity = erniegps.process_activity(activity)

            activity['activity_version'] = ACTIVITY_VERSION

            print("Created activity ( {0} )".format(create_activity_reason))

            #result = collection.replace_one(
                #activity_query, activity, upsert=True)
            #upserted_id = result.upserted_id
            #logging.debug("upserted_id: {0}".format(upserted_id))
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

            erniemail.activity_notify(activity, recipient, sender)
        else:
            logging.debug("Found activity")

    else:
        print("Skipping filename: {0}".format(filename))
print("created_count: {0}".format(created_count))
