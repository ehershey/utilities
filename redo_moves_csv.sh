#!/bin/bash
# Update moves.csv with all values from Moves Service (takes a long time to run)
#
# Requires $MOVES_ACCESS_TOKEN environment variable
# or crontab.env in same directory
#

MONTHLY_SLEEP_SECONDS=45

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
for year in $(seq 2013 2015)
do
  for month in $(seq -w 1 12)
  do
    date
    echo "starting $MONTHLY_SLEEP_SECONDS second sleep timer"
    sleep $MONTHLY_SLEEP_SECONDS &
    for day in $(seq -w 1 31)
    do
      echo $year$month$day:
      curl --silent "https://api.moves-app.com/api/1.1/user/summary/daily/$year$month$day?access_token=$MOVES_ACCESS_TOKEN" | ~ernie/git/utilities/print_moves_csv.py > $tempfile ; cat "$csvfile" >> $tempfile ; cat $tempfile | sort --key 5,5 --field-separator=, --reverse --numeric | sort --key=1,1 --field-separator=, --reverse --unique > $tempfile2
      ls -l $tempfile2 $csvfile
      wc -l $tempfile2 $csvfile
      if ! cmp -s $tempfile2 $csvfile
      then
        cat $tempfile2 > $csvfile
      else
        echo "No update to file content - not updating"
      fi
      rm $tempfile $tempfile2
    done
    date
    echo "waiting for sleep timer to finish"
    wait
    date
    echo "done"
  done
done
echo redo_moves_csv.sh finished
date
