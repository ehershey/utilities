#!/bin/sh
units_average=$(cut -f5 -d, ~/Dropbox/Web/moves.csv  | awk '{ total += $1; count++ } END { print total/count }' | sed 's/\..*//')
units_today=$(cut -f5 -d, ~/Dropbox/Web/moves.csv  | head -2 | tail -1 | sed 's/\..*//')

LOCKFILE=/tmp/mailed_unit_message.lock

echo "units_today: $units_today"
echo "units_average: $units_average"
if [ "$units_today" -gt "$units_average" ]
then
  if [ ! -e "$LOCKFILE" ]
  then
    echo "Surpassed unit average! (today: $units_today, average: $units_average)" | mail average_unit_checker@ernie.org
  fi
else
  rm -rf "$LOCKFILE"
fi

