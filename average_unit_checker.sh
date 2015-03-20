#!/bin/bash
#
# Email when daily calorie expenditure passes average and double average
#

export calories_column=$(head -1 ~/Dropbox/Web/moves.csv  | tr , \\n  | grep -n Calories | cut -f1 -d:)
echo "calories_column: $calories_column"

calories_average=$(cut -f$calories_column -d, ~/Dropbox/Web/moves.csv  | awk '{ total += $1; count++ } END { print total/count }' | sed 's/\..*//')
double_calories_average=$(cut -f$calories_column -d, ~/Dropbox/Web/moves.csv  | awk '{ total += 2*$1; count++ } END { print total/count }' | sed 's/\..*//')
calories_today=$(cut -f$calories_column -d, ~/Dropbox/Web/moves.csv  | head -2 | tail -1 | sed 's/\..*//')

LOCKFILE=/tmp/mailed_calorie_message.lock
DOUBLE_LOCKFILE=/tmp/mailed_double_calorie_message.lock

echo "calories_today: $calories_today"
echo "calories_average: $calories_average"
echo "double_calories_average: $double_calories_average"
if [ "$calories_today" -gt "$calories_average" ]
then
  if [ ! -e "$LOCKFILE" ]
  then
    echo "Surpassed calorie average! (today: $calories_today, average: $calories_average)" | mail average_calorie_checker@ernie.org
    touch "$LOCKFILE"
  fi
else
  rm -rf "$LOCKFILE"
fi

if [ "$calories_today" -gt "$double_calories_average" ]
then
  if [ ! -e "$DOUBLE_LOCKFILE" ]
  then
    echo "Surpassed DOUBLE calorie average! (today: $calories_today, average: $calories_average)" | mail average_calorie_checker@ernie.org
    touch "$DOUBLE_LOCKFILE"
  fi
else
  rm -rf "$DOUBLE_LOCKFILE"
fi
