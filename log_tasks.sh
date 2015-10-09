#!/bin/sh
#
# Log and show recent count of overdue todoist tasks
#

LOGFILE=/Users/ernie/Dropbox//Documents/10gen/Meetings/random.txt

date >> $LOGFILE

list_tasks.py  | wc -l >> $LOGFILE

tail $LOGFILE
