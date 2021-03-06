#!/bin/bash
#
# Add open house to calendar
#
# Usage:
# addopenhouse.sh [ --no-dupe-check ] <title> <date> <description> <duration - minutes> <location>
#
CALENDAR="Personal"

if [ "$1" = "--no-dupe-check" ]
then
  no_dupe_check="true"
  shift
else
  no_dupe_check=""
fi


TITLE="$1"
DATE="$2"
DESCRIPTION="$3"
DURATION="$4"
LOCATION="$5"

if [ ! "$LOCATION" ]
then
  echo "Usage: addopenhouse.sh <title> <date> <description> <duration> <location>"
  exit 2
fi

REMINDER=1440 # day

output="$(gcalcli --cache --calendar "$CALENDAR" search "\"$TITLE\"" --details url | grep .)"
if [ ! "$no_dupe_check" -a ! "$(echo "$output" | grep 'No Events Found...')" ]
then
  echo "Probable duplicate:"
  echo "$output"
  exit 2
fi

NOAPTTITLE="$(echo "$TITLE" | sed 's/ APT.*//')"
NOAPTTITLE="$(echo "$NOAPTTITLE" | sed 's/ apt.*//')"
NOAPTTITLE="$(echo "$NOAPTTITLE" | sed 's/ Apt.*//')"

output="$(gcalcli --cache --calendar "$CALENDAR" search "\"$NOAPTTITLE\"" --details url | grep .)"
if [ ! "$no_dupe_check" -a ! "$(echo "$output" | grep 'No Events Found...')" ]
then
  echo "Probable duplicate:"
  echo "$output"
  exit 2
fi

set -x
output="$(gcalcli add --calendar "$CALENDAR" --title "$TITLE" --when "$DATE" --duration "$DURATION" --description "$DESCRIPTION" --where "$LOCATION" --reminder "$REMINDER" --details url)"

url="$(echo "$output" | tr \ \\t \\n | grep http | head -1)"
if [ ! "$url" ]
then
  echo "Can't find url. output: $output"
  exit 5
fi
open $url
