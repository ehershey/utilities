#!/bin/bash
#
#
# Take gps log data exported via:
# mysqldump ernie_org gps_log --tab=gps_log --fields-terminated-by="," --fields-enclosed-by="\"" --lines-terminated-by="\r\n"
#
# Import it into mongodb to look like: 
# {
#   _id: blah,
# }
#
#
# SQL table columns are:
# entry_id, last_update, entry_date, longitude, latitude, entry_source, accuracy
