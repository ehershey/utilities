#!/bin/bash
# Update moves.csv with values from Moves Service
# 
# Requires $MOVES_ACCESS_TOKEN environment variable
# or crontab.env in same directory
#
if [ ! "$MOVES_ACCESS_TOKEN" ]
then
  . "$(dirname "$0")"/crontab.env
fi
if [ ! "$MOVES_ACCESS_TOKEN" ]
then
  echo "No \$MOVES_ACCESS_TOKEN defined."
  exit 2
fi
tempfile=$(mktemp /tmp/update_moves_csv.XXXXXX)
tempfile2=$(mktemp /tmp/update_moves_csv.XXXXXX)
csvfile=~ernie/Dropbox/Web/moves.csv
echo update_moves_csv.sh starting
date
if [ ! -e "$csvfile" ]
then
  touch "$csvfile"
fi
curl "https://api.moves-app.com/api/v1/user/summary/daily?pastDays=10&access_token=$MOVES_ACCESS_TOKEN" | ~ernie/git/utilities/print_moves_csv.py > $tempfile ; cat "$csvfile" >> $tempfile ; cat $tempfile | sort --key 5,5 --field-separator=, --reverse --numeric | sort --key=1,1 --field-separator=, --reverse --unique > $tempfile2
ls -l $tempfile2 $csvfile
if ! cmp -s $tempfile2 $csvfile
then
  cat $tempfile2 > $csvfile
else
  echo "No update to file content - not updating"
fi
echo update_moves_csv.sh finished
date
rm $tempfile $tempfile2
