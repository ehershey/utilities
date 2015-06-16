#!/bin/bash
set -o nounset
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

DATE=${2:-$TODAY}

tempfile="$(mktemp /tmp/registerrace.XXXXX)"
echo $tempfile

gcalcli --cache --cal "$CALENDAR" search --nolineart --nocolor --detail_description_width 200 "$TITLE (registered) $YEAR" --details all > "$tempfile"

title=$(grep ^$YEAR $tempfile | awk '{print $3,$4,$5,$6,$7,$8,$9,$10}')
echo "title: $title"

if [[ -s $tempfile && ! "$(grep 'No Events Found...' "$tempfile" )" && $title == *registered* ]]
then
  echo "Already registered:"
  cat "$tempfile"
  exit 2
fi

gcalcli --cache --cal "$CALENDAR" search --nolineart --nocolor --detail_description_width 200 "\"$TITLE\" $YEAR" --details all > "$tempfile"

count=$(grep Description: $tempfile | wc -l)

if [ "$count" -gt 1 ]
then
  echo "Too many matches, use more exact search term"
  echo "Dump of results:"
  cat $tempfile
  exit 3
fi

if [ "$count" -lt 1 ]
then
  echo "Too few matches, use better search term"
  exit 4
fi

description=$(grep -A 20 Description $tempfile | tail +3 | grep -v -- +----------------- | sed 's/^ *| //' | sed 's/  *|$//')
echo "description: >$description<"

title=$(grep ^$YEAR $tempfile | awk '{print $3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13}')
echo "title: $title"

if [[ ! "$title" ]]
then
  echo "Couldn't find title in tempfile: $tempfile"
  exit 5
fi

new_title=$(echo "$title" | sed "s/$YEAR/(registered) $YEAR/")
echo "new_title: $new_title"

new_description="$(echo "$description" | sed "s#Not registered as of ......[0-9]*#Registered on $DATE#" | grep . | tr \\n \ )"
echo "new_description: $new_description"

echo -e "t\n$new_title\nd\n$new_description\ns\nq"
echo -e "t\n$new_title\nd\n$new_description\ns\nq" | gcalcli --cal "$CALENDAR" edit "\"$title\""

#output="$(gcalcli add --cal "$CALENDAR" --title "$TITLE" --when "$DATE" --duration "$DURATION" --description "$URLNot registered as of $TODAY" --where "$LOCATION" --reminder "$REMINDER" --details url)"

#url="$(echo "$output" | tr \ \\t \\n | grep http | head -1)"
#if [ ! "$url" ]
#then
  #echo "Can't find url. output: $output"
  #exit 5
#fi
#open $url
