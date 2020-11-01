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
from types import SimpleNamespace
import stravalib
import pickle
import time
import datetime

autoupdate_version = 112

DB_URL = 'mongodb://localhost:27017/'

DB_NAME = 'strava'
COLLECTION_NAME = 'activities'

CLIENT_ID = 33845
CLIENT_SECRET = '49818c053c8adb0d8fb38270d4ae9cadc05ad0e7'

PICKLE_FILE = os.environ['HOME'] + "/.strava_pickle"

ACTIVITY_VERSION = 0.1

stravaclient = Client()

PROCESSED_DATES = {}


def upload_activity(gpx_xml=None,
                    name=None,
                    activity_type=None):
    init_strava()
    try:
        return stravaclient.upload_activity(activity_file=gpx_xml,
                                            name=name,
                                            data_type='gpx',
                                            activity_type=activity_type)
    except stravalib.exc.RateLimitExceeded as e:
        timeout = e.timeout
        print("Rate limit error. Sleeping {timeout} seconds".format(timeout=timeout))
        print()
        time.sleep(timeout)
        return stravaclient.upload_activity(activity_file=gpx_xml,
                                            name=name,
                                            data_type='gpx',
                                            activity_type=activity_type)


def get_args():
    """ Parse command line args """
    parser = argparse.ArgumentParser(
        description='Store Strava activities in db')
    parser.add_argument(
        '--weeks_back',
        required=False,
        default=0.3,
        help='Number of weeks back to search Strava (3rd and last precedence)',
        type=float)
    parser.add_argument(
        '--num_weeks_to_process',
        required=False,
        default=None,
        help='Number of weeks to process, starting with weeks_back (3rd and last precedence)',
        type=int)
    parser.add_argument(
        '--date',
        required=False,
        default=None,
        help='Do a single day (2nd precedence; after activity-id)',
        type=datetime.date.fromisoformat)
    parser.add_argument(
        '--activity-id',
        required=False,
        default=None,
        help='Process a single activity (1st precedence)',
        type=int)
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
        '--force_reauth',
        default=False,
        help='Re-auth to strava',
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


def get_oauth_data(oauth_code=None, config_data={}, force_access_token_refresh=False,
                   force_reauth=False):

    if 'access_token' in config_data and not force_reauth:
        logging.debug("Found auth config data in pickle")
    else:
        logging.debug("No auth config in pickle or force_reauth=true, doing auth dance")

        if oauth_code and not force_reauth:
            code = oauth_code
        else:

            authorize_url = stravaclient.authorization_url(client_id=CLIENT_ID,
                                                           redirect_uri='http://strava.ernie.org',
                                                           scope=['activity:read',
                                                                  'activity:write'])

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
                       lone_detailed_activity=None,
                       lone_activity_id=None):

    """
    process activities - precedence is:
    1) The single passed in detailed activity
       - presumably from a recent upload
       - try this first because it's the cheapest and doesn't hit the strava API
       - script doesn't support this mode because it assumes this much detail
         isn't available via cli
    2) The single passed in activity ID
       - presumably from a web hook
       - will always download latest version of activity from strava
    3) Hit strava and download anything on the passed in day (GMT)
    4) Hit strava and grab weeks at a time
    """

    logging.debug("num_weeks_to_process: %s", num_weeks_to_process)
    if lone_activity_id is not None:
        logging.debug("lone_activity_id: %s", lone_activity_id)
        # oof - from
        # https://stackoverflow.com/questions/16279212/how-to-use-dot-notation-for-dict-in-python
        activities = [SimpleNamespace(id=lone_activity_id)]
    elif lone_detailed_activity is not None:
        logging.debug("lone_detailed_activity: %s", lone_detailed_activity)
        activities = [lone_detailed_activity]
    else:
        # Search by after/before timestamps;

        one_day = datetime.timedelta(days=1)
        if date is None:
            after = datetime.datetime.now() - datetime.timedelta(weeks=weeks_back)

            if num_weeks_to_process is not None:
                before = after + datetime.timedelta(weeks=num_weeks_to_process)
            else:
                before = None
        else:
            after = datetime.datetime.combine(date, datetime.datetime.min.time())
            before = after + one_day

        # Strava's date filtering seems to over-exclude activities that overlap
        # the before or after dates at all so always subtract a day from 'after'
        # and add a day to 'before' to include extra days

        if before is not None:
            before = before + one_day
        after = after - one_day

        logging.debug(f"Download activities after: {after}")
        logging.debug(f"Download activities before: {before}")

        activities = stravaclient.get_activities(after=after, before=before)

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

            # print dates processed
            # used to trigger re-generating summary data by re-importing data for the day
            for field in ['start_date_local', 'end_date_local']:
                timestamp = activity[field]
                dateonly = timestamp.date()
                PROCESSED_DATES[dateonly] = True

        else:
            logging.debug("Found pre-existing activity in db")
    print("created_count: {0}".format(created_count))


def main():
    """
    Read arguments, do auth, dl from strava, save to db
    """

    args = get_args()

    if args.date and (args.num_weeks_to_process is not None or args.weeks_back != 0.3):
        logging.warning("Letting --date override --num_weeks_to_process and --weeks_back")

    update_db(debug=args.debug,
              oauth_code=args.oauth_code,
              redo=args.redo,
              force_access_token_refresh=args.force_access_token_refresh,
              force_reauth=args.force_reauth,
              num_weeks_to_process=args.num_weeks_to_process,
              weeks_back=args.weeks_back,
              lone_activity_id=args.activity_id,
              date=args.date)

    for processed_date in PROCESSED_DATES:
        print(f"date: {processed_date}")


def get_collection():

    mongoclient = MongoClient(DB_URL)

    database = mongoclient[DB_NAME]

    return database[COLLECTION_NAME]


def init_strava(oauth_code=None, force_access_token_refresh=False,
                force_reauth=False):

    config_data = setup_pickle()

    get_oauth_data(oauth_code=oauth_code,
                   config_data=config_data,
                   force_access_token_refresh=force_access_token_refresh,
                   force_reauth=force_reauth)


def update_db(debug=False,
              oauth_code=None,
              redo=False,
              force_access_token_refresh=False,
              force_reauth=False,
              num_weeks_to_process=None,
              weeks_back=1,
              date=None,
              lone_activity_id=None,
              lone_detailed_activity=None):
    """
    does it all
    """

    if debug:
        logging.getLogger().setLevel(getattr(logging, "DEBUG"))

    init_strava(oauth_code=oauth_code,
                force_reauth=force_reauth,
                force_access_token_refresh=force_access_token_refresh)
    try:
        process_activities(weeks_back=weeks_back,
                           collection=get_collection(),
                           redo=redo,
                           num_weeks_to_process=num_weeks_to_process,
                           date=date,
                           lone_detailed_activity=lone_detailed_activity,
                           lone_activity_id=lone_activity_id)
    except stravalib.exc.RateLimitExceeded as e:
        timeout = e.timeout
        print("Rate limit error. Sleeping {timeout} seconds".format(timeout=timeout))
        print()
        time.sleep(timeout)
        process_activities(weeks_back=weeks_back,
                           collection=get_collection(),
                           redo=redo,
                           num_weeks_to_process=num_weeks_to_process,
                           date=date,
                           lone_detailed_activity=lone_detailed_activity,
                           lone_activity_id=lone_activity_id)


if __name__ == '__main__':
    main()
