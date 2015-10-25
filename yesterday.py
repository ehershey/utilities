#!/usr/bin/python
#
# Print the timestamp 24 hours ago
#
#
import datetime
now = datetime.datetime.now()
yesterday = now + datetime.timedelta(days=-1)
print datetime.datetime.strftime(yesterday, "%c")
