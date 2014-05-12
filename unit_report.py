#!/usr/bin/env python
import datetime
import os
import os.path
import sys
import time
from os.path import expanduser
import urllib2
import numerous_apikey
home = expanduser("~ernie")


TEMPLATE_FILENAME = "%s/unit-report-template.html" % os.path.dirname(os.path.realpath(__file__)) 
MOVES_CSV_FILENAME = "%s/Dropbox/Web/moves.csv" % home

placeholder = {}

units_average = os.popen("cut -f5 -d, %s| awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_today = os.popen("cut -f5 -d, %s  | head -2 | tail -1" % MOVES_CSV_FILENAME).read().rstrip()
units_yesterday = os.popen("cut -f5 -d, %s  | head -3 | tail -1" % MOVES_CSV_FILENAME).read().rstrip()
units_average_2013 = os.popen("grep ^2013- %s | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_average_2014 = os.popen("grep ^2014- %s | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()
units_average_7days = os.popen("head -8 %s | tail -7 | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }'" % MOVES_CSV_FILENAME).read().rstrip()


units_today_2013_diff = float(units_today) - float(units_average_2013)
units_yesterday_2013_diff = float(units_yesterday) - float(units_average_2013)
units_average_2013_diff = float(units_average) - float(units_average_2013)
units_average_7days_2013_diff = float(units_average_7days) - float(units_average_2013)
units_average_2014_2013_diff = float(units_average_2014) - float(units_average_2013)

if units_today_2013_diff > 0:
    placeholder['today_class'] = "positive_diff"
else:
    placeholder['today_class'] = "negative_diff"

if units_yesterday_2013_diff > 0:
    placeholder['yesterday_class'] = "positive_diff"
else:
    placeholder['yesterday_class'] = "negative_diff"

if units_average_7days_2013_diff > 0:
    placeholder['7days_class'] = "positive_diff"
else:
    placeholder['7days_class'] = "negative_diff"

if units_average_2014_2013_diff > 0:
    placeholder['2014_class'] = "positive_diff"
else:
    placeholder['2014_class'] = "negative_diff"

if units_average_2013_diff > 0:
    placeholder['alltime_class'] = "positive_diff"
else:
    placeholder['alltime_class'] = "negative_diff"


placeholder['units_today_2013_diff'] = units_today_2013_diff 
placeholder['units_today'] = units_today 
placeholder['units_yesterday_2013_diff'] = units_yesterday_2013_diff 
placeholder['units_yesterday'] = units_yesterday 
placeholder['units_average'] = units_average 
placeholder['units_average_2013_diff'] = units_average_2013_diff 
placeholder['units_average_2013'] = units_average_2013 
placeholder['units_average_2014'] = units_average_2014 
placeholder['units_average_2014_2013_diff'] = units_average_2014_2013_diff 
placeholder['units_average_7days'] = units_average_7days 
placeholder['units_average_7days_2013_diff'] = units_average_7days_2013_diff 
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

    # Report to numerous
    #
    # TODO: move this out of report script
    #
    metric_id = "6359390767342201980"
    url = "https://api.numerousapp.com/v1/metrics/%s/events" % metric_id
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm = 'Numerous',
                                  uri = url, 
                                  user = numerous_apikey.apikey,
                                  passwd='')
    opener = urllib2.build_opener(auth_handler)
    # ...and install it globally so it can be used with urlopen.
    urllib2.install_opener(opener)

    values = """ { "value": %s, "onlyIfChanged": true } """ % units_today
    headers = { 'Content-Type': 'application/json' }
    request = urllib2.Request(url, data=values, headers=headers)
    response_body = urllib2.urlopen(request).read()
    sys.stderr.write(response_body)
