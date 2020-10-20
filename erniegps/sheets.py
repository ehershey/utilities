"""
Interact with Google Sheets
"""

from __future__ import print_function
import logging
import dateutil.parser
import httplib2
import os
from apiclient import discovery
import googleapiclient.errors
from pymongo import MongoClient

from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import requests
import re
import simplejson as json
import subprocess
import sys
import time


SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = os.path.dirname(__file__) + '/client_secret.json'
CREDENTIALS_FILE = os.path.dirname(__file__) + '/erniegps.sheets_credentials.json'
APPLICATION_NAME = 'erniegps.sheets'

LOGGER = logging.getLogger(name=APPLICATION_NAME)

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


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
        credentials = tools.run_flow(flow, store, flags=None)
        LOGGER.debug('Storing credentials to ' + credential_path)
    return credentials


def insert_record_into_sheet(google_credentials, record, spreadsheet_id, sheet_name):
    http = google_credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    request = service.spreadsheets().get(spreadsheetId=spreadsheet_id)
    try:
        response = request.execute()
    except googleapiclient.errors.HttpError as e:
        if "Quota exceeded" in str(e):
            raise(e)
        else:
            response = request.execute()

    LOGGER.debug("Found spreadsheet")

    found_sheet = None
    for sheet in response['sheets']:
        if sheet['properties']['title'] == sheet_name:
            found_sheet = sheet
            found_sheet_id = sheet['properties']['sheetId']
    if found_sheet:
        LOGGER.debug("Found sheet in spreadsheet")
        LOGGER.debug("found_sheet: {found_sheet}".format(found_sheet=found_sheet))
    else:
        raise Exception("Couldn't find sheet named: {name}".format(name=sheet_name))

    dateRange = '{name}!A:A'.format(name=sheet_name)
    request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=dateRange)
    try:
        response = request.execute()
    except googleapiclient.errors.HttpError as e:
        if "Quota exceeded" in str(e):
            raise(e)
        else:
            response = request.execute()

    if 'values' in response:
        dates_in_sheet = response['values']
    else:
        dates_in_sheet = []

    # experiment: only use verbose date to ensure uniqueness
    # try:
    #     date_to_parse = record['Date']
    #     if "$date" in date_to_parse:
    #         date_to_parse = date_to_parse['$date']
    #     logging.debug("date_to_parse: {date_to_parse}".format(date_to_parse=date_to_parse))
    #     record_date = dateutil.parser.parse(date_to_parse)
    # except TypeError as error:
    #     date_to_parse = record['Verbose Date']
    #     if "$date" in date_to_parse:
    #         date_to_parse = date_to_parse['$date']
    #     logging.debug("date_to_parse: {date_to_parse}".format(date_to_parse=date_to_parse))
    #     record_date = dateutil.parser.parse(date_to_parse)
    date_to_parse = record['Verbose Date']
    logging.debug("date_to_parse: {date_to_parse}".format(date_to_parse=date_to_parse))
    record_date = dateutil.parser.parse(date_to_parse)

    # raise Exception(record_date)
    LOGGER.debug("record_date: {record_date}".format(record_date=record_date))
    record_date_rownum = None

    row_num = 0
    matching_row_num = None
    for date in dates_in_sheet[1:]:
        row_num += 1
        # unwind the list within a list (dates_in_sheet is a range with one column)
        #
        if len(date) > 0:
            date = date[0]
            LOGGER.debug("date: {date}".format(date=date))
            try:
                compare_sheet_date = dateutil.parser.parse(date).replace(hour=0, minute=0, second=0,
                                                                         tzinfo=None)
                compare_record_date = record_date.replace(hour=0, minute=0, second=0, tzinfo=None)
                LOGGER.debug("compare_sheet_date: {compare_sheet_date}".format(
                              compare_sheet_date=compare_sheet_date))
                LOGGER.debug("compare_record_date: {compare_record_date}".format(
                             compare_record_date=compare_record_date))
                if compare_sheet_date == compare_record_date:
                    LOGGER.debug("match!")
                    matching_row_num = row_num
                    break
            except TypeError as error:
                LOGGER.error("unparseable date in sheet: {date}".format(date=date))
                # ignore unparseable dates
    LOGGER.debug("matching_row_num: {matching_row_num}".format(matching_row_num=matching_row_num))

    headerRange = '{name}!A1:ZZ1'.format(name=sheet_name)
    headerRequest = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,
                                                        range=headerRange)
    try:
        headerResponse = headerRequest.execute()
    except googleapiclient.errors.HttpError as e:
        # try again
        if "Quota exceeded" in str(e):
            raise(e)
        else:
            headerResponse = headerRequest.execute()
    if 'values' in headerResponse:
        headers = headerResponse['values'][0]
    else:
        headers = []
    LOGGER.debug("headers: {headers}".format(headers=headers))
    row = []
    for header in headers:
        if header in record:
            value = record[header]
            if type(value) == float or type(value) == int:
                value_type = "numberValue"
            else:
                value_type = "stringValue"
                value = str(value)
            row.append({"userEnteredValue": {value_type: value}})
        else:
            row.append({"userEnteredValue": {"numberValue": 0}})
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

    # updateRange = ""
    # updateRange = '{sheet_name}!A{row_num}'.format(
    #   sheet_name=sheet_name, row_num=matching_row_num)
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
                             # "fields": "Date, Walking",
                             # "fields": ", ".join(headers),
                             # "rows":  row ,
                             # "fields": "0", # Date, Walking, Walking Seconds",
                             "fields": "*",
                             "rows": [{"values": [row]}],
                         }
                     })

    update_request = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body=batch_update_spreadsheet_request_body)
    try:
        update_response = update_request.execute()
    except googleapiclient.errors.HttpError as e:
        if "Quota exceeded" in str(e):
            raise(e)
        else:
            update_response = update_request.execute()
    LOGGER.debug("response: {response}".format(response=response))
