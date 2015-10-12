#!/bin/sh
#
# Log and show recent count of overdue todoist tasks
#

LOGFILE=/Users/ernie/Dropbox//Documents/10gen/Meetings/random.txt

date >> $LOGFILE

(list_tasks.py  ; list_tasks.py --filter Yesterday) | sort -u | wc -l >> $LOGFILE

tail $LOGFILE
