#!/bin/bash
#
# Add Race to calendar
#
NYRR_TITLE_SELECTOR="h2.title"
NYRR_DATE_SELECTOR="p.full-width span"



# Use cache_get if available, else curl
#
if which cache_get &>/dev/null
then
  CURL="cache_get 86400"
else
  CURL="curl --silent --location" 
fi

echo "CURL: $CURL"

# Validate selectors
#
expected_title="NYRR Al Gordon 4-Mile"

get_race_title() {
  url="$1"
  returned_title="$($CURL "$url" | pup "$NYRR_TITLE_SELECTOR" text{})" 
  returned_title="$(echo -n "$returned_title" | sed 's/[ 	]*$//'; )"
  echo "$returned_title"
}
returned_title="$(get_race_title "http://www.nyrr.org/races-and-events/2015/nyrr-al-gordon-4-mile")"
if [ "$returned_title" != "$expected_title" ]
then
  echo "Test command failed! Got $returned_title, expected $expected_title"
  exit 2
fi

expected_date="Saturday, February 21, 2015 8:00am"

get_race_date() {
  url="$1"
  returned_date="$($CURL "$url" | pup "$NYRR_DATE_SELECTOR" text{})" 
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	]*$//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/^[ 	]*//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/^[ 	]*//'; )"
  returned_date="$(echo -n "$returned_date" | tr -d \\n)"
  echo "$returned_date"
}
returned_date="$(get_race_date "http://www.nyrr.org/races-and-events/2015/nyrr-al-gordon-4-mile")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi

url="$1"

title="$(get_race_title "$url")"
date="$(get_race_date "$url")"
addrace.sh "$title" "$date" "$url" 
