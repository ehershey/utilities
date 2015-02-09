#!/bin/sh
#
# Add Race to calendar
# Usage: 
# 
# addrace.sh <title> <date> <url> [ <duration - minutes, default 120> [ <location - default NYC> [ <reminder - minutes, default 10080 (one week)> ] ] ]
CALENDAR="Rides and Races"
TODAY=$(date +%D)
YEAR=$(date +%Y)

TITLE="$1"
DATE="$2"
URL="$3"

if [ ! "$URL" ]
then
  echo "Usage: addrace.sh <title> <date> <url> [ <duration - minutes, default 120> [ <location - default NYC> [ <reminder - minutes, default 10080 (one week)> ] ] ]"
  exit 2
fi

DEFAULT_DURATION=120
DEFAULT_LOCATION="NYC"
DEFAULT_REMINDER=10080 # week

if [ "$4" ]
then
  DURATION="$4"
else
  DURATION="$DEFAULT_DURATION"
fi

if [ "$4" ]
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

set -x
output="$(gcalcli add --cal "$CALENDAR" --title "$TITLE" --when "$DATE" --duration "$DURATION" --description "$URLNot registered as of $TODAY" --where "$LOCATION" --reminder "$REMINDER" --details url)"

url="$(echo "$output" | tr \ \\t \\n | grep http | head -1)"
open $url
