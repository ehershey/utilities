#!/usr/bin/env python
import datetime
import os

placeholder = {}

placeholder['units_average'] = os.popen("cut -f5 -d, ~/Dropbox/Web/moves.csv  | awk '{ total += $1; count++ } END { print total/count }' | sed 's/\..*//'").read()
placeholder['units_today'] = os.popen("cut -f5 -d, ~/Dropbox/Web/moves.csv  | head -2 | tail -1 | sed 's/\..*//'").read()
placeholder['units_average_2013'] = os.popen("grep ^2013- ~/Dropbox/Web/moves.csv | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }' | sed 's/\..*//'").read()
placeholder['units_average_2014'] = os.popen("grep ^2014- ~/Dropbox/Web/moves.csv | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }' | sed 's/\..*//'").read()
placeholder['units_average_7days'] = os.popen("head -8 ~/Dropbox/Web/moves.csv | tail -7 | cut -f5 -d, | awk '{ total += $1; count++ } END { print total/count }' | sed 's/\..*//'").read()
placeholder['now'] = str(datetime.datetime.now())


# echo "units_today: $units_today"
# echo "units_average: $units_average"
# echo "units_average_2013: $units_average_2013"
# echo "units_average_2014: $units_average_2014"
# echo "units_average_7days: $units_average_7days"

TEMPLATE_FILENAME = "%s/unit-report-template.html" % os.path.dirname(os.path.realpath(__file__)) 

if __name__ == '__main__':
    is_release_candidate = False

    with open (TEMPLATE_FILENAME, "r") as myfile:
          template=myfile.read()


    formated = template.format(**placeholder)
    print formated
