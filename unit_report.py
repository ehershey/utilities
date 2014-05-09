#!/usr/bin/env python
import datetime
import os
import os.path
import time
from os.path import expanduser
home = expanduser("~")


TEMPLATE_FILENAME = "%s/unit-report-template.html" % os.path.dirname(os.path.realpath(__file__)) 
MOVES_CSV_FILENAME = "%s/Dropbox/Web/moves.csv" % home

placeholder = {}

units_average = os.popen("cut -f5 -d, %s| awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read()
units_today = os.popen("cut -f5 -d, %s  | head -2 | tail -1" % MOVES_CSV_FILENAME).read()
units_yesterday = os.popen("cut -f5 -d, %s  | head -3 | tail -1" % MOVES_CSV_FILENAME).read()
units_average_2013 = os.popen("grep ^2013- %s | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read()
units_average_2014 = os.popen("grep ^2014- %s | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read()
units_average_7days = os.popen("head -8 %s | tail -7 | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read()


units_today_2013_diff = float(units_today) - float(units_average_2013)
units_yesterday_2013_diff = float(units_yesterday) - float(units_average_2013)

placeholder['units_today_2013_diff'] = units_today_2013_diff 
placeholder['units_today'] = units_today 
placeholder['units_yesterday_2013_diff'] = units_yesterday_2013_diff 
placeholder['units_yesterday'] = units_yesterday 
placeholder['units_average'] = units_average 
placeholder['units_average_2013'] = units_average_2013 
placeholder['units_average_2014'] = units_average_2014 
placeholder['units_average_7days'] = units_average_7days 
placeholder['now'] = time.ctime()
placeholder['moves_csv_modified'] = time.ctime(os.path.getmtime(MOVES_CSV_FILENAME))


# echo "units_today: $units_today"
# echo "units_average: $units_average"
# echo "units_average_2013: $units_average_2013"
# echo "units_average_2014: $units_average_2014"
# echo "units_average_7days: $units_average_7days"


if __name__ == '__main__':
    is_release_candidate = False

    with open (TEMPLATE_FILENAME, "r") as myfile:
          template=myfile.read()


    formated = template.format(**placeholder)
    print formated
