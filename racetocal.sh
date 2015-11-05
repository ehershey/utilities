#!/bin/bash
#
# Add Race to calendar
#
NYRR_TITLE_SELECTOR="h2.title"
NYRR_DATE_SELECTOR="p.full-width span"

NYCRUNS_TITLE_SELECTOR=".race-display-name"
NYCRUNS_DATE_SELECTOR=".race-display-date"
NYCRUNS_ADDRESS_SELECTOR=".race-display-address"

RNR_DATE_SELECTOR="h2:contains(\"General Info\") + p + p"
RNR_TITLE_SELECTOR="h2:contains(\"General Info\") + p"

EVENTBRITE_TITLE_SELECTOR="span.summary"
EVENTBRITE_DATE_SELECTOR="span.dtstart"

set -o nounset

# Use cache_get if available, else curl
#
if which cache_get &>/dev/null
then
  CURL="cache_get 86400"
else
  CURL="curl --silent --location"
fi

# Make sure pup is available
#
if which pup &>/dev/null
then
  PUP="pup --plain"
else
  echo "pup utility required"
  exit 3
fi

get_race_title() {
  url="$1"
  returned_title="$($CURL "$url" | $PUP "$NYRR_TITLE_SELECTOR" text{})"
  if [ ! "$returned_title" ]
  then
    returned_title="$($CURL "$url" | $PUP "$NYCRUNS_TITLE_SELECTOR" text{})"
  fi

  if [ ! "$returned_title" ]
  then
    returned_title="$($CURL "$url" | $PUP "$RNR_TITLE_SELECTOR" text{})"
  fi

  if [ ! "$returned_title" ]
  then
    returned_title="$($CURL "$url" | $PUP "$EVENTBRITE_TITLE_SELECTOR" text{})"
  fi

  # Trim trailing whitespace
  #
  returned_title="$(echo -n "$returned_title" | sed 's/[ 	]*$//' )"

  # Grab only first line
  #
  returned_title="$(echo -n "$returned_title" | head -1 )"
  echo "$returned_title"
}

get_race_date() {
  url="$1"
  returned_date="$($CURL "$url" | $PUP "$NYRR_DATE_SELECTOR" text{})"
  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$NYCRUNS_DATE_SELECTOR" text{})"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$RNR_DATE_SELECTOR" text{})"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$EVENTBRITE_DATE_SELECTOR" text{})"
  fi

  returned_date="$(echo -n "$returned_date" | tr A-Z a-z | sed 's/start time://g' | sed 's/start\.//g')"
  returned_date="$(echo -n "$returned_date" | tr \\n \ )"
  returned_date="$(echo -n "$returned_date" | sed 's/half marathon starts at//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/full marathon starts at//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/race[- ]day.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/5k start//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ 5k//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ 5 miler.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ - / /g')"
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	][ 	]*/ /g'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/;.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/^[ 	]*//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	]*$//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ from / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ the / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ begins at / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ to .*//'; )"
  echo "$returned_date"
}

get_race_address() {
  url="$1"
  returned_address="$($CURL "$url" | $PUP "$NYCRUNS_ADDRESS_SELECTOR" text{})"

  # Trim trailing whitespace
  #
  returned_address="$(echo -n "$returned_address" | sed 's/[ 	]*$//' )"

  # Grab only last line
  #
  returned_address="$(echo -n "$returned_address" | tail -1 )"

  returned_address="$(echo -n "$returned_address" | sed 's/^[ 	]*//'; )"
  echo "$returned_address"
}


# Validate selectors and scraping logic
#
expected_title="NYRR Al Gordon 4M"

returned_title="$(get_race_title "http://www.nyrr.org/races-and-events/2015/nyrr-al-gordon-4-mile")"
if [ "$returned_title" != "$expected_title" ]
then
  echo "Test command failed! Got $returned_title, expected $expected_title"
  exit 2
fi

expected_date="saturday, february 21, 2015 8:00am"
returned_date="$(get_race_date "http://www.nyrr.org/races-and-events/2015/nyrr-al-gordon-4-mile")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi

expected_title="City of Yonkers Marathon, Half Marathon, 5K"
returned_title="$(get_race_title "https://nycruns.com/races/?race=the-yonkers-marathon-2015")"
if [ "$returned_title" != "$expected_title" ]
then
  echo "Test command failed! Got $returned_title, expected $expected_title"
  exit 2
fi

expected_date="october 18, 2015 8:00 a.m."
returned_date="$(get_race_date "https://nycruns.com/races/?race=the-yonkers-marathon-2015")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi

expected_date="february 28, 2016 8:00 am"
returned_date="$(get_race_date "https://nycruns.com/races/?race=nycruns-central-park-marathon-2016")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi

expected_title="Run the River 5K - Icahn Stadium/Randall's Island Park"
returned_title="$(get_race_title "http://www.eventbrite.com/e/run-the-river-5k-icahn-stadiumrandalls-island-park-registration-17885348559?nomo=1")"
if [ "$returned_title" != "$expected_title" ]
then
  echo "Test command failed! Got $returned_title, expected $expected_title"
  exit 2
fi

expected_date="saturday, october 24, 2015 8:30 am"
returned_date="$(get_race_date "http://www.eventbrite.com/e/run-the-river-5k-icahn-stadiumrandalls-island-park-registration-17885348559?nomo=1")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi



url="$1"

title="$(get_race_title "$url")"
date="$(get_race_date "$url")"
address="$(get_race_address "$url")"

if [ ! "$title" ]
then
  echo "Can't determine title"
  exit 3
fi
if [ ! "$date" ]
then
  echo "Can't determine date"
  exit 4
fi
addrace.sh "$title" "$date" "$url" "" "$address"
