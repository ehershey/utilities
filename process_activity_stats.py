#!/usr/bin/env python
#
#
# Watch for tcx files saved by Tapiriik.
# When they come in, do some analysis and
# email results to myself.

import erniegps
import logging
import os
import pymongo
from pymongo import MongoClient

activity_dir = "{0}/Dropbox/Apps/tapiriik".format(os.environ['HOME'])
db_url = 'mongodb://localhost:27017/'

db_name = 'ernie_org'
collection_name = 'stat_activities'

# re-process activities without this version #
ACTIVITY_VERSION = 1

client = MongoClient(db_url)

db = client[db_name]

collection = db[collection_name]

for basename in os.listdir(activity_dir):
    filename = os.path.join(activity_dir, basename)
    if "tcx" in filename:
        print("Processing filename: {0}".format(filename))

        activity = collection.find_one({"filename": filename})
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
            create_activity_reason = "Version in DB too low ({0} < {0})".format(activity['activity_version'], ACTIVITY_VERSION)

        if create_activity:
            activity = erniegps.read_activity(filename)
            activity = erniegps.process_activity(activity)

            activity['activity_version'] = ACTIVITY_VERSION

            print("Created activity ( {0} )".format(create_activity_reason))

            inserted_id = collection.insert_one(activity)
            logging.debug("inserted_id: {0}".format(inserted_id))

            # exit()
        else:
            print("Found activity")
        print("is_negative_split: {0}".format(activity['is_negative_split']))
        print("negative_split_depth: {0}".format(activity['negative_split_depth']))
        print(u"notes: {0}".format(activity['notes']))
        print("activity_type: {0}".format(activity['activity_type']))
        print("verbose_starttime: {0}".format(activity['verbose_starttime']))
        print("verbose_distance: {0}".format(activity['verbose_distance']))
    else:
        print("Skipping filename: {0}".format(filename))
