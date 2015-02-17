#!/bin/sh
#
# Update status of race in calendar to registered
# Usage:
#
# registerrace.sh <title> [ <registration date> ]
CALENDAR="Rides and Races"
TODAY=$(date +%D)
YEAR=$(date +%Y)

TITLE="$1"

if [ ! "$TITLE" ]
then
  echo "Usage: registerrace.sh <title> [ <registration date> ]"
  exit 2
fi

if [ "$2" ]
then
  DATE="$2"
else
  DATE="$TODAY"
fi

REGISTERED_TITLE="$TITLE (registered)"

tempfile="$(mktemp /tmp/registerrace.XXXXX)"

gcalcli --cache --cal "$CALENDAR" search "\"$REGISTERED_TITLE\" $YEAR" --details all > "$tempfile"
if [ -s $tempfile -a ! "$(grep 'No Events Found...' "$tempfile" )" ]
then
  echo "Already registered:"
  cat "$tempfile"
  exit 2
fi

gcalcli --cache --cal "$CALENDAR" search "\"$TITLE\" $YEAR" --details all > "$tempfile"

#output="$(gcalcli add --cal "$CALENDAR" --title "$TITLE" --when "$DATE" --duration "$DURATION" --description "$URLNot registered as of $TODAY" --where "$LOCATION" --reminder "$REMINDER" --details url)"

#url="$(echo "$output" | tr \ \\t \\n | grep http | head -1)"
#if [ ! "$url" ]
#then
  #echo "Can't find url. output: $output"
  #exit 5
#fi
#open $url
