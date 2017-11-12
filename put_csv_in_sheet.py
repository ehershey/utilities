#!/usr/bin/env python2.7

from __future__ import print_function
import csv
import httplib2
import logging
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

logging.basicConfig(format=("%(asctime).19s %(levelname)s %(filename)s:"
                                    "%(lineno)s %(message)s "))

LOGGER = logging.getLogger(name = 'put_csv_in_sheet')

LOGGER.setLevel(logging.INFO)

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

LOGGER.info("Starting")

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/put_csv_in_sheet.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'

CSV_FILENAME = "{home}/Dropbox/Web/moves.csv".format(home = os.environ['HOME'])


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'put_csv_in_sheet.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    """Blow away a sheet content with the content of a CSV

    """
    credentials = get_credentials()
    LOGGER.info("Got credentials")
    http = credentials.authorize(httplib2.Http())
    LOGGER.info("Authorized credentials")
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    LOGGER.info("Found service")

    spreadsheetId = '1WpC1w_0iAl4sO7sQP5CwsvPAXx0WHt3GlOj-3G3VfL8'

    sheetName='All moves data'

    request = service.spreadsheets().get(spreadsheetId=spreadsheetId)
    response = request.execute()

    LOGGER.info("Found spreadsheet")

    found_sheet = None
    for sheet in response['sheets']:
        if sheet['properties']['title'] == sheetName:
            found_sheet = sheet
    if found_sheet:
            LOGGER.info("Found sheet in spreadsheet")
    else:
        LOGGER.fatal("Couldn't find sheet named: {name}".format(name=sheetName))

    rangeName = '{name}!A:ZZ'.format(name=sheetName)

    # Clear the sheet first
    #
    result = service.spreadsheets().values().clear(
                spreadsheetId=spreadsheetId, range=rangeName, body={}).execute()

    LOGGER.info("Cleared range")


    # Then populate it
    values = []

    csv_filename = CSV_FILENAME
    with open(csv_filename) as csv_fd:
        csv_reader = csv.reader(csv_fd)
        for row in csv_reader:
            values.append(row)

    body = {
       'values': values
    }

    LOGGER.info("Read data from csv file")

    result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheetId, range=rangeName,
                    valueInputOption="USER_ENTERED", body=body).execute()

    LOGGER.info("Populated data in sheet")

    print(result)


if __name__ == '__main__':
    main()
