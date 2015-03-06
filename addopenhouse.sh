#!/bin/bash
#
# Add open house to calendar
# Usage: 
# 
# addopenhouse.sh <title> <date> <url> <duration - minutes> <location>
CALENDAR="Personal"

TITLE="$1"
DATE="$2"
URL="$3"
DURATION="$4"
LOCATION="$5"

if [ ! "$LOCATION" ]
then
  echo "Usage: addopenhouse.sh <title> <date> <url> <duration> <location>"
  exit 2
fi

REMINDER=1440 # day

output="$(gcalcli --cache --cal "$CALENDAR" search "\"$TITLE\"" --details url | grep .)"
if [ ! "$(echo "$output" | grep 'No Events Found...')" ]
then
  echo "Probable duplicate:"
  echo "$output"
  exit 2
fi

NOAPTTITLE="$(echo "$TITLE" | sed 's/ APT.*//')"
NOAPTTITLE="$(echo "$NOAPTTITLE" | sed 's/ apt.*//')"
NOAPTTITLE="$(echo "$NOAPTTITLE" | sed 's/ Apt.*//')"

output="$(gcalcli --cache --cal "$CALENDAR" search "\"$NOAPTTITLE\"" --details url | grep .)"
if [ ! "$(echo "$output" | grep 'No Events Found...')" ]
then
  echo "Probable duplicate:"
  echo "$output"
  exit 2
fi

set -x
output="$(gcalcli add --cal "$CALENDAR" --title "$TITLE" --when "$DATE" --duration "$DURATION" --description "$URL" --where "$LOCATION" --reminder "$REMINDER" --details url)"

url="$(echo "$output" | tr \ \\t \\n | grep http | head -1)"
if [ ! "$url" ]
then
  echo "Can't find url. output: $output"
  exit 5
fi
open $url
