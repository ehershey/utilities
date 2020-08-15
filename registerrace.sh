#!/bin/bash
set -o nounset
set -o errexit

URL_COLUMN=5
TITLE_COLUMN=9
DESCRIPTION_COLUMN=24

#
# Update status of race in calendar to registered
# Usage:
#
# registerrace.sh <search_string> [ <event year> [ <registration date> ]]

CALENDAR="Rides and Races"
TODAY=$(date +%D)

SEARCH_STRING="${1:-}"
YEAR="${2:-}"

if [ ! "$SEARCH_STRING" ]
then
  echo "Usage: registerrace.sh <search_string> [ <event year> [ <registration date> ]]"
  exit 2
fi
if [ ! "$YEAR" ]
then
  YEAR=$(date +%Y)
fi

DATE=${3:-$TODAY}

# Error if date looks like a year
#
if echo "$DATE" | grep -xq '[0-9][0-9][0-9][0-9]'
then
  echo "Date looks funny ($DATE). Is it a year?"
  exit 2
fi

# Error if search string looks like a date or year
#
if echo "$SEARCH_STRING" | grep -xq '[0-9][0-9][0-9][0-9]'
then
  echo "Search string looks funny ($SEARCH_STRING). Is it a year?"
  exit 2
fi
if echo "$SEARCH_STRING" | grep '^[^/]*/[^/]*/[^/]$'
then
  echo "Search string looks funny ($SEARCH_STRING). Is it a date?"
  exit 2
fi


tempfile="$(mktemp /tmp/registerrace.XXXXX)"
echo $tempfile

gcalcli --calendar "$CALENDAR" search --tsv --nostarted --military --nocolor "$SEARCH_STRING (registered) $YEAR" --details all > "$tempfile"

#title=$(grep ^$YEAR $tempfile | awk '{print $3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21}')
returned_title="$(cut -f$TITLE_COLUMN "$tempfile")"
url="$(cut -f$URL_COLUMN "$tempfile")"


if [[ ! "$returned_title" ]]
then
  echo "Couldn't find returned_title"
  exit 5
fi

echo "returned_title: $returned_title"
echo "url: $url"

if [[ -s $tempfile && ! "$(grep 'No Events Found...' "$tempfile" )" && $returned_title == *registered* ]]
then
  echo "Already registered"
  echo "$url"
  exit 2
fi

gcalcli --calendar "$CALENDAR" search --nostarted --military --nocolor "$SEARCH_STRING $YEAR" --details all > "$tempfile"

count=$(grep Location: $tempfile | wc -l)

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

#description=$(grep -A 20 Description $tempfile | tail +3 | grep -v -- +----------------- | grep -v -- ────────── | sed 's/\│//g' )
description="$(gcalcli --calendar "$CALENDAR" search --tsv --nocolor "$SEARCH_STRING $YEAR" --details all | cut -f$DESCRIPTION_COLUMN -d\	 | sed 's/<br[^>]*>/ /g' | sed 's/<[^>]*>//g')"
echo "description: >$description<"

new_title=$(echo "$returned_title" | sed "s/$YEAR/(registered) $YEAR/")
echo "new_title: $new_title"

#new_description="$(echo "$description" | sed "s#Not registered as of ......[0-9]*#Registered on $DATE#" | grep . | tr \\n \  | sed 's/\\n/ /g')"
new_description="$(echo "$description" | sed "s#Not registered as of ......[0-9]*#Registered on $DATE#" | sed 's/\\n/\\\\n/g')"

# Account for no "Not registered" note in original event
#
if ! echo "$new_description" | grep -qi registered
then
  new_description="$new_description\\nRegistered on $DATE"
fi

echo "new_description: $new_description"

if ! gcalcli --version 2>&1 | grep -q ernie
then
  echo
  echo "ERROR!"
  echo "Saving events requires modified gcalcli for multiline descriptions">&2
  echo "Try running this:">&2
  echo "patch -p0 < ~/Dropbox/Misc/gcalcli.patch">&2
  exit 5
fi


echo -e "t\n$new_title\nd\n$new_description\ns\nq"
echo -e "t\n$new_title\nd\n$new_description\ns\nq" | gcalcli --calendar "$CALENDAR" edit "\"$returned_title\""

echo
echo "$url"

#output="$(gcalcli add --calendar "$CALENDAR" --title "$SEARCH_STRING" --when "$DATE" --duration "$DURATION" --description "$URLNot registered as of $TODAY" --where "$LOCATION" --reminder "$REMINDER" --details url)"

#url="$(echo "$output" | tr \ \\t \\n | grep http | head -1)"
#if [ ! "$url" ]
#then
  #echo "Can't find url. output: $output"
  #exit 5
#fi
#open $url
