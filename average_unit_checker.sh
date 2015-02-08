#!/bin/bash

export calories_column=$(head -1 ~/Dropbox/Web/moves.csv  | tr , \\n  | grep -n Calories | cut -f1 -d:)
echo "calories_column: $calories_column"

units_average=$(cut -f$calories_column -d, ~/Dropbox/Web/moves.csv  | awk '{ total += $1; count++ } END { print total/count }' | sed 's/\..*//')
double_units_average=$(cut -f$calories_column -d, ~/Dropbox/Web/moves.csv  | awk '{ total += 2*$1; count++ } END { print total/count }' | sed 's/\..*//')
units_today=$(cut -f$calories_column -d, ~/Dropbox/Web/moves.csv  | head -2 | tail -1 | sed 's/\..*//')

LOCKFILE=/tmp/mailed_unit_message.lock
DOUBLE_LOCKFILE=/tmp/mailed_double_unit_message.lock

echo "units_today: $units_today"
echo "units_average: $units_average"
echo "double_units_average: $double_units_average"
if [ "$units_today" -gt "$units_average" ]
then
  if [ ! -e "$LOCKFILE" ]
  then
    echo "Surpassed unit average! (today: $units_today, average: $units_average)" | mail average_unit_checker@ernie.org
    touch "$LOCKFILE"
  fi
else
  rm -rf "$LOCKFILE"
fi

if [ "$units_today" -gt "$double_units_average" ]
then
  if [ ! -e "$DOUBLE_LOCKFILE" ]
  then
    echo "Surpassed DOUBLE unit average! (today: $units_today, average: $units_average)" | mail average_unit_checker@ernie.org
    touch "$DOUBLE_LOCKFILE"
  fi
else
  rm -rf "$DOUBLE_LOCKFILE"
fi
