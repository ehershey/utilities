#!/usr/bin/env python
#
#
# Watch for tcx files saved by Tapiriik.
# When they come in, do some analysis and
# email results to myself.
#

import os
import erniegps
import pymongo
from pymongo import MongoClient

activity_dir = "/home/ernie/Dropbox/Apps/tapiriik"
db_url = 'mongodb://localhost:27017/'

db_name = 'ernie_org'
collection_name = 'stat_activities'

client = MongoClient(db_url)

db = client[db_name]

collection = db[collection_name]

for basename in os.listdir(activity_dir):
    filename = os.path.join(activity_dir, basename)
    print("filename:", filename)

    activity = collection.find_one({"filename": filename})
    print("activity:", activity)
    if activity is None:
        activity = erniegps.read_activity(filename)
        activity = erniegps.process_activity(activity)

        print("activity:", activity)

        inserted_id = collection.insert_one(activity)
        print("inserted_id: {0}".format(inserted_id))

        exit()
