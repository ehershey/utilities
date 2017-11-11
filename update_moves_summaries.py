#!/usr/bin/env python2.7
# Update moves summary collection with values from Moves App
#
# Requires $MOVES_ACCESS_TOKEN and MONGODB_URI environment variables
#

from apiclient import discovery
import argparse
import datetime
import dateutil.parser
import httplib2
import logging
import os
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from pymongo import MongoClient
import requests
import re
import simplejson as json
import subprocess
import sys
import time




COLLECTION = "summaries"
DB = "moves"

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = os.path.dirname(__file__) + '/client_secret.json'
CREDENTIALS_FILE = os.path.dirname(__file__) + '/sheets.googleapis.com-python-quickstart.json'
APPLICATION_NAME = 'update_moves_summaries.py'

logging.basicConfig(format=("%(asctime).19s %(levelname)s %(filename)s:"
                                    "%(lineno)s %(message)s "))

# reuse oauth app name for logging config
LOGGER = logging.getLogger(name = APPLICATION_NAME)


logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

LOGGER.info("Starting")


parser = argparse.ArgumentParser(description='Update Database from Moves API')
parser.add_argument('--verbose', action='store_true', required=False, help='Show verbose logging', default = False);
parser.add_argument('--redo', action='store_true', required=False, help='Load old data', default = False);
parser.add_argument('--limit', required=False, help='Process at most this many days', type=int);
parser.add_argument('--month', required=False, help='Month for which to load old data (format: NN)', type=int);
parser.add_argument('--year', required=False, help='Year for which to load old data (format: NN)', type=int);
parser.add_argument('--spreadsheet_id', required=False, help='Google Sheets document ID to update');
parser.add_argument('--sheet_name', required=False, help='Google Sheets sheet name (within sheet document) to update');
args = parser.parse_args()

redo = args.redo
month = args.month
year = args.year

limit = args.limit

spreadsheet_id = args.spreadsheet_id
sheet_name = args.sheet_name

verbose = args.verbose

if verbose:
    LOGGER.setLevel(logging.DEBUG)
else:
    LOGGER.setLevel(logging.INFO)

if sheet_name and not spreadsheet_id:
    raise Exception("--spreadsheet_id is required if --sheet_name is passed")
if spreadsheet_id and not sheet_name:
    raise Exception("--sheet_name is required if --spreadsheet_id is passed")

#
if "MOVES_ACCESS_TOKEN" not in os.environ:
    raise Exception("No $MOVES_ACCESS_TOKEN defined.")
if "MONGODB_URI" not in os.environ:
    raise Exception("No $MONGODB_URI defined.")
MOVES_ACCESS_TOKEN = os.environ["MOVES_ACCESS_TOKEN"]
MONGODB_URI = os.environ["MONGODB_URI"]

mongo_client = MongoClient(MONGODB_URI)

db = mongo_client[DB]

collection = db[COLLECTION]

processed_num = 0

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """

    credential_path = CREDENTIALS_FILE
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        LOGGER.debug('Storing credentials to ' + credential_path)
    return credentials

def insert_record_into_sheet(record):
    http = google_credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    request = service.spreadsheets().get(spreadsheetId=spreadsheet_id)
    response = request.execute()

    LOGGER.debug("Found spreadsheet")

    found_sheet = None
    for sheet in response['sheets']:
        if sheet['properties']['title'] == sheet_name:
            found_sheet = sheet
            found_sheet_id = sheet['properties']['sheetId']
    if found_sheet:
            LOGGER.debug("Found sheet in spreadsheet")
            LOGGER.debug("found_sheet: {found_sheet}".format(found_sheet = found_sheet))
    else:
        raise Exception("Couldn't find sheet named: {name}".format(name=sheet_name))

    dateRange = '{name}!A:A'.format(name=sheet_name)
    request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=dateRange)
    response = request.execute()

    # TODO: Change code below to process the `response` dict:
    dates_in_sheet = response['values']

    record_date = record['Date']
    LOGGER.debug("record_date: {record_date}".format(record_date=record_date))
    record_date_rownum = None

    row_num = 0
    matching_row_num = None
    for date in dates_in_sheet[1:]:
        row_num+=1
        # unwind the list within a list (dates_in_sheet is a range with one column)
        #
        if len(date) > 0:
            date = date[0]
            LOGGER.debug("date: {date}".format(date=date))
            try:
                if dateutil.parser.parse(date).replace(hour = 0, minute = 0, second = 0) == record_date.replace(hour = 0, minute = 0 , second = 0):
                    LOGGER.debug("match!")
                    matching_row_num = row_num
                    break
            except TypeError as error:
                LOGGER.error("unparseable date in sheet: {date}".format(date=date))
                # ignore unparseable dates
    LOGGER.debug("matching_row_num: {matching_row_num}".format(matching_row_num=matching_row_num))

    headerRange = '{name}!A1:ZZ1'.format(name=sheet_name)
    headerRequest = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=headerRange)
    headerResponse = headerRequest.execute()
    headers = headerResponse['values'][0]
    LOGGER.debug("headers: {headers}".format(headers=headers))
    row = []
    for header in headers:
        if header in record:
            row.append({"userEnteredValue": { "stringValue": str(record[header]) } })
        else:
            row.append({"userEnteredValue": { "stringValue": str(0) } } )
    LOGGER.debug("row: {row}".format(row=row))

    batch_update_spreadsheet_request_body = {
                'requests': []
                }
    if matching_row_num is None:
        # insert a row as row 1

        batch_update_spreadsheet_request_body['requests'].append(
                    {
                        "insertDimension":
                        {
                            "range":
                            {
                                "sheetId":
                                found_sheet_id,
                                "dimension":
                                "ROWS",
                                "startIndex":
                                1,
                                "endIndex":
                                2
                            },
                        }
                    })
        matching_row_num = 1

    #updateRange = ""
    #updateRange = '{sheet_name}!A{row_num}'.format(sheet_name = sheet_name, row_num = matching_row_num)
    updateRange = {
            "sheetId":
            found_sheet_id,
            "startRowIndex":
            matching_row_num,
            "endRowIndex":
            matching_row_num + 1,
            }
 
    batch_update_spreadsheet_request_body['requests'].append(
                     {
                         "updateCells":
                         {
                             "range": updateRange,
                             #"fields": "Date, Walking",
                             #"fields": ", ".join(headers),
                             #"rows":  row ,
                             #"fields": "0", # Date, Walking, Walking Seconds",
                             "fields": "*", 
                             "rows": [ { "values": [ row ] } ],
                         }
                     })



    update_request = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_spreadsheet_request_body)
    update_response = update_request.execute()

    LOGGER.debug("response: {response}".format(response = response))



def process_month(year, month):
    url = "https://api.moves-app.com/api/1.1/user/summary/daily/{year}{month:02d}?access_token={token}".format(token=MOVES_ACCESS_TOKEN, month = month, year = year)
    try:
       process_url(url)
    except Exception as error:
        LOGGER.error("Error: {error}".format(error=error))


def process_url(url):
    LOGGER.debug("url: {url}".format(url=url))

    r = requests.get(url)
    if r.status_code != 200:
        LOGGER.error("Bad status code")
        LOGGER.error("r.text: {text}".format(text = r.text))
        raise Exception("Bad status code: {code}".format(code = r.status_code))

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

    summaries = []
    for index, summary in enumerate(response):
        summaries.append(summary)
    for summary in reversed(summaries):
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
                    calories += float(activity_calories)
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
                record[verbose_activity_name_duration] = float(("%.2f" % duration_seconds))
                # sys.stdout.write("%.2f" % duration_seconds)

        record['Calories'] = float(calories)
        LOGGER.info("record: {record}".format(record = record))
        # sys.stdout.write(",%d" % calories)
        # sys.stdout.write("\n")
        filter = {"Date": record['Date']}
        result = collection.replace_one(filter, record, upsert=True)
        LOGGER.info("Inserted into DB!")

        if spreadsheet_id and sheet_name:
            insert_record_into_sheet(record)
            LOGGER.info("Inserted into spreadsheet!")

        global processed_num
        processed_num += 1
        LOGGER.info("processed {processed_num} days (limit: {limit})".format(processed_num = processed_num, limit = limit))

        if args.limit and processed_num >= args.limit:
            exit()


google_credentials = get_credentials()

if redo:
    if year:
        if month:
            process_month(year, month)
        else:
            for month in range(1,13):
                process_month(year, month)
    else:
        if month:
            for year in range(2013,datetime.datetime.now().year+1):
                process_month(year, month)
        else:
            for year in range(2013,datetime.datetime.now().year+1):
                for month in range(1,13):
                    process_month(year, month)
else:
    url = "https://api.moves-app.com/api/1.1/user/summary/daily?pastDays=10&access_token={token}".format(token=MOVES_ACCESS_TOKEN)
    process_url(url)

