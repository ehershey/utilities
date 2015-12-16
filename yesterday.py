#!/usr/bin/python
#
# Print a timestamp representing 24 hours ago from now
#
#
import datetime
now = datetime.datetime.now()
yesterday = now + datetime.timedelta(days=-1)
print datetime.datetime.strftime(yesterday, "%c")
