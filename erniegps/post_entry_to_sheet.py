#!/usr/bin/env python3
# This should be kinder to the sheets API and hit it less.
# Maybe cache summaries that have made it in already?
# Maybe add last updated dates to summaries?
#
"""
Take summary entry and add to google sheets

sample input:

{
    "Walking": "6.76mi",
    "Cycling": "95.14mi",
    "Running Seconds": 4676.0,
    "Calories": 5402.0,
    "Running": "5.61mi",
    "Date": {"$date": "2017-12-15T00:00:00.000Z"},
    "Walking Seconds": 8909.0,
    "Cycling Seconds": 23204.0,
    "entry_source": "Arc Export"
}
#
"""

import argparse
import logging
import json
import select
import sys
import sheets


def main():
    """ do it all """

    parser = argparse.ArgumentParser(description='post daily summary data to google sheets')
    parser.add_argument('--debug', help='Display debugging info', action='store_true')
    parser.add_argument('--filename', help='File to read', default=None)
    parser.add_argument('--spreadsheet_id', required=False,
                        help='Google Sheets document ID to update')
    parser.add_argument('--sheet_name', required=False,
                        help='Google Sheets sheet name (within sheet document) to update')
    args = parser.parse_args(args=sys.argv[1:], namespace=argparse.Namespace())

    if args.debug:
        logging.getLogger().setLevel(getattr(logging, "DEBUG"))
        logging.debug("Debug logging enabled")

    if args.filename:
        logging.debug("reading from file")
        summary_file = open(args.filename)
    else:
        logging.debug("reading from stdin")
        summary_file = sys.stdin

    spreadsheet_id = args.spreadsheet_id
    sheet_name = args.sheet_name

    if sheet_name and not spreadsheet_id:
        raise Exception("--spreadsheet_id is required if --sheet_name is passed")
    if spreadsheet_id and not sheet_name:
        raise Exception("--sheet_name is required if --spreadsheet_id is passed")

    # try:
    raw_json = summary_file.read()
    logging.debug("len(raw_json): " + str(len(raw_json)))
    if len(raw_json) <= 2:
        logging.debug("no data; exiting")
        return

    summary = json.loads(raw_json)
    # except json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

    logging.debug("read input")

    logging.debug(f"summary: {summary}")
    (summary)

    sys.argv = sys.argv[0:0]
    google_credentials = sheets.get_credentials()
    sheets.insert_record_into_sheet(google_credentials, summary, spreadsheet_id, sheet_name)


if __name__ == '__main__':
    main()
