#!/bin/sh
#
#
# Given a JIRA-exported XLS file, move a "Description" column in the last column
# to its own row, and rename the file from .xls to .html
#
# 

xlsfile="$1"

if [ ! "$xlsfile" ] 
then
  echo "Usage: $0 <xls file>"
  exit 2
fi

if [ ! "`echo \"$xlsfile\" | grep \\.xls$`" ]
then
  echo "Error: File doesn't have .xls extension."
  exit 3
fi

echo "Moving to "
