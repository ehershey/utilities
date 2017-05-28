#!/bin/bash
# Re-udate moves.csv with values from Moves Service (takes a long time to run)
#
# Requires $MOVES_ACCESS_TOKEN environment variable
# or crontab.env in same directory
#
#
# Usage:
# redo_moves_csv.sh [ <year> [ <month> [ <day> ] ] ]
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

CURRENT_YEAR=$(date +%Y)
OLDEST_YEAR=2013

# YEAR
#
if [ "$1" ]
then
  year_range="$1"
  shift
else
  year_range=$(seq $OLDEST_YEAR $CURRENT_YEAR)
fi

# MONTH
#
if [ "$1" ]
then
  month_range="$1"
  shift
else
  month_range=$(seq -w 1 12)
fi

# DATE
#
if [ "$1" ]
then
  day_range="$1"
  shift
else
  day_range=$(seq -w 1 31)
fi



for year in $year_range
do
  for month in $month_range
  do
    date
    echo "starting $MONTHLY_SLEEP_SECONDS second sleep timer"
    sleep $MONTHLY_SLEEP_SECONDS &
    for day in $day_range
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
