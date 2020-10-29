#!/bin/bash
#
# Add Race to calendar
# Usage:
#
# addrace.sh <title> <date> <url> [ <duration - minutes, default 120> [ <location - default NYC> [ <reminder - minutes, default 10080 (one week)> ] ] ]
#
# autoupdate_version = 15

set -o pipefail
set -o errexit

CALENDAR="Rides and Races"
TODAY=$(date +%D)

TITLE="$1"
DATE="$2"
URL="$3"

if [ ! "$URL" ]
then
  echo "Usage: addrace.sh <title> <date> <url> [ <duration - minutes, default 120> [ <location - default NYC> [ <reminder - minutes, default 10080 (one week)> ] ] ]"
  exit 2
fi

DATE="$(echo "$DATE" | sed 's/ at / /')"

YEAR=$(perl -MPOSIX=strftime -MDate::Parse -e 'print(strftime("%Y",localtime(str2time(shift))));' "$DATE")

NOW_YEAR=$(date +%Y)

# forget why I added this but if it's a past year just let it be a past year
#20201029
#
# if [ "$YEAR" -lt "$NOW_YEAR" ]
# then
  # YEAR=$NOW_YEAR
# fi

#if ! echo "$DATE" | grep -q "$YEAR"
#then
  #echo "Year not in date, unsupported ($DATE / $YEAR)"
  #exit 2
#fi

DEFAULT_DURATION=120
DEFAULT_LOCATION="NYC"
DEFAULT_START_TIME="8am"
DEFAULT_REMINDER=10080 # week

if [ "$4" ]
then
  DURATION="$4"
else
  DURATION="$DEFAULT_DURATION"
fi

if [ "$5" ]
then
  LOCATION="$5"
else
  LOCATION="$DEFAULT_LOCATION"
fi

if [ "$6" ]
then
  REMINDER="$6"
else
  REMINDER="$DEFAULT_REMINDER"
fi




if [ ! "$(echo "$TITLE" | grep $YEAR)" ]
then
  TITLE="$TITLE $YEAR"
fi

REGISTERED_TITLE="$(echo "$TITLE" | sed "s/ $YEAR$/(registered) $YEAR/")"

output="$(gcalcli --calendar "$CALENDAR" search "\"$TITLE\"" --details url | grep .)"
if [ ! "$(echo "$output" | grep 'No Events Found...')" ]
then
  echo "Probable duplicate:"
  echo "$output"
  exit 2
fi

output="$(gcalcli --calendar "$CALENDAR" search "\"$REGISTERED_TITLE\"" --details url | grep .)"
if [ ! "$(echo "$output" | grep 'No Events Found...')" ]
then
  echo "Probable duplicate:"
  echo "$output"
  exit 2
fi

if echo "$DATE" | grep -q " " && ( echo "$DATE" | grep -q : || echo "$DATE" | grep -q [0-9][ap]\.\?m\.\?)
then
  DATEWITHSTARTTIME="$DATE"
else
  DATEWITHSTARTTIME="$DATE $DEFAULT_START_TIME"
fi

output="$(gcalcli --calendar "$CALENDAR" add --title "$TITLE" --when "$DATEWITHSTARTTIME" --duration "$DURATION" --description "$URL

Not registered as of $TODAY" --where "$LOCATION" --reminder "$REMINDER" --details url)"

url="$(echo "$output" | tr \ \\t \\n | grep http | head -1)"
if [ ! "$url" ]
then
  echo "Can't find url. output: $output"
  exit 2
fi
open $url
