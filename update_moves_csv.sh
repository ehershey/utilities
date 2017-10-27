#!/bin/bash
# Update moves.csv with values from Moves App
#
tempfile=$(mktemp /tmp/update_moves_csv.XXXXXX)
tempfile2=$(mktemp /tmp/update_moves_csv.XXXXXX)
csvfile=~ernie/Dropbox/Web/moves.csv

fields="Date,Walking,Walking Seconds,Cycling,Cycling Seconds,Car,Car Seconds,Running,Running Seconds,Airplane,Airplane Seconds,Transport,Transport Seconds,Swimming,Swimming Seconds,Unknown,Unknown Seconds,Calories"

echo update_moves_csv.sh starting
date
if [ ! -e "$csvfile" ]
then
  touch "$csvfile"
fi

mongoexport  --quiet --fields="$fields" --type=csv --db moves --collection summaries | sed 's/\(201.-..-..\)T/\1 /g' | sed 's/00:00:00.000Z/00:00:00/g' | sort -ur >> "$tempfile2"

ls -l "$tempfile2" $csvfile
if ! cmp -s $tempfile2 $csvfile
then
  cat $tempfile2 > $csvfile
else
  echo "No update to file content - not updating"
fi
echo update_moves_csv.sh finished
date
rm $tempfile $tempfile2
