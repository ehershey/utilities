#!/bin/sh
#
# Call the python file, passing spreadsheet info and a limit of 1
#
# This is intended to be called in limited circumstances when updating one value is expected
# 
#
"$(dirname "$0")"/update_moves_summaries.py --spreadsheet_id $MARATHON_SPREADSHEET_ID --sheet_name "All moves data" --limit 1
