#!/usr/bin/env python3

import os


def get_db_url():
    """ get DB URI - default to localhost """
    if "MONGODB_URI" in os.environ:
        return os.environ["MONGODB_URI"]
    return "localhost"


autoupdate_version = 8

STRAVA_DB = "strava"
LIVETRACK_DB = "livetrack"

ACTIVITY_COLLECTION = "activities"
SESSION_COLLECTION = "session"
