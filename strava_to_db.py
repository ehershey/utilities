#!/usr/bin/env python3
"""
Download Strava workouts and save in database
"""

import argparse
import logging
import os
# import erniemail
import erniegps
from pymongo import MongoClient
from stravalib.client import Client
import stravalib
import pickle
import time
import datetime

autoupdate_version = 41

DB_URL = 'mongodb://localhost:27017/'

DB_NAME = 'strava'
COLLECTION_NAME = 'activities'

CLIENT_ID = 33845
CLIENT_SECRET = '49818c053c8adb0d8fb38270d4ae9cadc05ad0e7'

PICKLE_FILE = os.environ['HOME'] + "/.strava_pickle"

ACTIVITY_VERSION = 0.1

stravaclient = Client()


def get_args():
    """ Parse command line args """
    parser = argparse.ArgumentParser(
        description='Store Strava activities in db')
    parser.add_argument(
        '--weeks_back',
        required=False,
        default=1,
        help='Number of weeks back to search Strava',
        type=int)
    parser.add_argument(
        '--num_weeks_to_process',
        required=False,
        default=None,
        help='Number of weeks to process, starting with weeks_back',
        type=int)
    parser.add_argument(
        '--date',
        required=False,
        default=None,
        help='Do a single day (mutually exclusive with weeks_back and num_weeks_to_process)',
        type=datetime.date.fromisoformat)
    parser.add_argument(
        '--oauth_code',
        required=False,
        help='Code for oauth to skip initial auth request and prompt',
        type=str)
    parser.add_argument(
        '--force_access_token_refresh',
        default=False,
        help='Refresh access token regardless of expiration time',
        action='store_true')
    parser.add_argument(
        '--redo',
        default=False,
        help='Process file whether in DB already or not',
        action='store_true')
    parser.add_argument(
        '--debug',
        default=False,
        help='Print debugging info to stderr',
        action='store_true')
    args = parser.parse_args()
    return args


def save_pickle(config_data={}):
    with open(PICKLE_FILE, 'wb') as f:
        pickle.dump(config_data, f)


def load_pickle():
    with open(PICKLE_FILE, 'rb') as f:
        config_data = pickle.load(f)
    return config_data


def setup_pickle():
    if os.path.exists(PICKLE_FILE):
        logging.debug("found pickle file, loading it")
        return load_pickle()
    else:
        logging.debug("No pickle file, creating it")
        save_pickle()
        return {}


def get_oauth_data(oauth_code=None, config_data={}, force_access_token_refresh=False):

    if 'access_token' in config_data:
        logging.debug("Found auth config data in pickle")
    else:
        logging.debug("No auth config in pickle, doing auth dance")

        if oauth_code:
            code = oauth_code
        else:

            authorize_url = stravaclient.authorization_url(client_id=CLIENT_ID,
                                                           redirect_uri='http://strava.ernie.org')

            print("authorize_url: {authorize_url}".format(authorize_url=authorize_url))

            # Extract the code from your webapp response
            code = input("Enter code from redirect: ")

        token_response = stravaclient.exchange_code_for_token(client_id=CLIENT_ID,
                                                              client_secret=CLIENT_SECRET,
                                                              code=code)
        config_data['access_token'] = token_response['access_token']
        config_data['refresh_token'] = token_response['refresh_token']
        config_data['expires_at'] = token_response['expires_at']

    logging.debug("config_data:")
    logging.debug(config_data)

    if time.time() > config_data['expires_at'] or force_access_token_refresh is True:
        logging.debug("Refreshing access token")
        refresh_response = \
            stravaclient.refresh_access_token(client_id=CLIENT_ID,
                                              client_secret=CLIENT_SECRET,
                                              refresh_token=config_data['refresh_token'])
        config_data['access_token'] = refresh_response['access_token']
        config_data['refresh_token'] = refresh_response['refresh_token']
        config_data['expires_at'] = refresh_response['expires_at']
    else:
        logging.debug("Not refreshing access token")

    logging.debug("config_data:")
    logging.debug(config_data)

    logging.debug("Saving auth config data to pickle file")

    save_pickle(config_data)

    # Now store that short-lived access token somewhere (a database?)
    stravaclient.access_token = config_data['access_token']
    # You must also store the refresh token to be used later on to obtain another valid access token
    # in case the current is already expired
    # stravaclient.refresh_token = config_data['refresh_token']
    # An access_token is only valid for 6 hours, store expires_at somewhere and
    # check it before making an API call.
    stravaclient.token_expires_at = config_data['expires_at']


def process_activities(weeks_back=1,
                       collection=None,
                       redo=False,
                       num_weeks_to_process=None,
                       date=None,
                       lone_detailed_activity=None):

    """
    process activities - precendece is:
    1) The single passed in detailed activity (presumably from a recent upload)
    2) Hit strava and download anything on the passed in day (GMT)
    3) Hit strava and grab weeks at a time
    """

    if lone_detailed_activity is not None:
        activities = [lone_detailed_activity]
    else:
        # search by after/before timestamps
        if date is None:

            after = datetime.datetime.now() - datetime.timedelta(weeks=weeks_back)

            if num_weeks_to_process is not None:
                before = after + datetime.timedelta(weeks=num_weeks_to_process)
            else:
                before = None
        else:
            after = datetime.datetime.combine(date, datetime.datetime.min.time())
            before = before + datetime.timedelta(days=1)

        activities = stravaclient.get_activities(after=after, before=before)

        logging.debug("Download activities after: {after}".format(after=after))
        logging.debug("Download activities before: {before}".format(before=before))

    created_count = 0
    for activity in activities:

        # for field in EXTRACT_FIELDS:

        # if activity.type == 'Run':
        #     print("{activity.start_date_local},
        #     {activity.distance}, {activity.moving_time}".format(activity=activity))

        activity_query = {"strava_id": activity.id}
        db_activity = collection.find_one(activity_query)
        create_activity = False
        create_activity_reason = None
        if lone_detailed_activity:
            detail_activity = lone_detailed_activity
        else:
            try:
                detail_activity = stravaclient.get_activity(activity.id)
            # stravalib.exc.AccessUnauthorized: Unauthorized: Authorization Error:
            # [{'resource': 'Application', 'field': '', 'code': 'invalid'}]
            except stravalib.exc.AccessUnauthorized as e:
                wait = 30
                logging.warn("Access unauthorized error on get_activity()")
                logging.warn("Waiting {wait} seconds and retrying".format(wait=wait))
                time.sleep(wait)
                detail_activity = stravaclient.get_activity(activity.id)

        # TODO: use streams to detect gaps to allow other activity data to pass through
        # between gaps in strava activities (e.g. if walking around during stopped
        # ride/run on garmin watch)
        #
        # streams = stravaclient.get_activity_streams(activity.id,
        # types=['moving'], resolution='high')
        # logging.debug("streams: %s", streams)

        logging.debug("db_activity: %s", db_activity)
        logging.debug("detail_activity: %s", detail_activity)
        if db_activity is None:
            create_activity = True
            create_activity_reason = "No activity in DB"
        elif 'activity_version' not in db_activity:
            create_activity = True
            create_activity_reason = "No version in DB"
        elif db_activity['activity_version'] < ACTIVITY_VERSION:
            create_activity = True
            create_activity_reason = "Version in DB too low ({0} < {1})".format(
                db_activity['activity_version'], ACTIVITY_VERSION)
        elif redo:
            create_activity = True
            create_activity_reason = "Redo flag passed"

        if create_activity:
            logging.debug("Saving activity: %s", activity)
            activity = erniegps.process_strava_activity(detail_activity)

            activity['activity_version'] = ACTIVITY_VERSION

            logging.debug("Created activity ( %s )", create_activity_reason)

            result = collection.replace_one(
                activity_query, activity, upsert=True)
            upserted_id = result.upserted_id
            logging.debug("upserted_id: %s", upserted_id)
            # only used for printing
            created_count += 1

            print(activity)

        else:
            logging.debug("Found pre-existing activity in db")
    print("created_count: {0}".format(created_count))


def main():
    """
    Read arguments, do auth, dl from strava, save to db
    """

    args = get_args()

    if args.date and (args.num_weeks_to_process is not None or args.weeks_back != 1):
        logging.warning("Letting --date override --num_weeks_to_process and --weeks_back")

    update_db(debug=args.debug,
              oauth_code=args.oauth_code,
              redo=args.redo,
              force_access_token_refresh=args.force_access_token_refresh,
              num_weeks_to_process=args.weeks_back, weeks_back=args.weeks_back,
              date=args.date)


def update_db(debug=False,
              oauth_code=None,
              redo=False,
              force_access_token_refresh=False,
              num_weeks_to_process=1,
              weeks_back=1,
              date=None):
    """
    does it all
    """

    if debug:
        logging.getLogger().setLevel(getattr(logging, "DEBUG"))

    mongoclient = MongoClient(DB_URL)

    database = mongoclient[DB_NAME]

    collection = database[COLLECTION_NAME]

    config_data = setup_pickle()

    get_oauth_data(oauth_code=oauth_code,
                   config_data=config_data,
                   force_access_token_refresh=force_access_token_refresh)

    try:
        process_activities(weeks_back=weeks_back,
                           collection=collection,
                           redo=redo,
                           num_weeks_to_process=num_weeks_to_process,
                           date=date)
    except stravalib.exc.RateLimitExceeded as e:
        timeout = e.timeout
        print("Rate limit error. Sleeping {timeout} seconds".format(timeout=timeout))
        print()
        time.sleep(timeout)
        main()


if __name__ == '__main__':
    main()
