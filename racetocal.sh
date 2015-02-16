#!/bin/bash
#
# Add Race to calendar
#
NYRR_TITLE_SELECTOR="h2.title"
NYCRUNS_TITLE_SELECTOR=".race-display-name"
NYRR_DATE_SELECTOR="p.full-width span"
NYCRUNS_DATE_SELECTOR=".race-display-date"



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

# Validate selectors
#
expected_title="NYRR Al Gordon 4M"

get_race_title() {
  url="$1"
  returned_title="$($CURL "$url" | $PUP "$NYRR_TITLE_SELECTOR" text{})"
  if [ ! "$returned_title" ]
  then
    returned_title="$($CURL "$url" | $PUP "$NYCRUNS_TITLE_SELECTOR" text{})"
  fi

  # Trim trailing whitespace
  #
  returned_title="$(echo -n "$returned_title" | sed 's/[ 	]*$//' )"

  # Grab only first line
  #
  returned_title="$(echo -n "$returned_title" | head -1 )"
  echo "$returned_title"
}
returned_title="$(get_race_title "http://www.nyrr.org/races-and-events/2015/nyrr-al-gordon-4-mile")"
if [ "$returned_title" != "$expected_title" ]
then
  echo "Test command failed! Got $returned_title, expected $expected_title"
  exit 2
fi


get_race_date() {
  url="$1"
  returned_date="$($CURL "$url" | $PUP "$NYRR_DATE_SELECTOR" text{})" 
  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$NYCRUNS_DATE_SELECTOR" text{})" 
  fi
  returned_date="$(echo -n "$returned_date" | tr A-Z a-z | sed 's/start time://g' | sed 's/start\.//g')"
  returned_date="$(echo -n "$returned_date" | tr \\n \ )"
  returned_date="$(echo -n "$returned_date" | sed 's/half marathon starts at//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/full marathon starts at//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	][ 	]*/ /g'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/;.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/^[ 	]*//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	]*$//'; )"
  echo "$returned_date"
}
expected_date="saturday, february 21, 2015 8:00am"
returned_date="$(get_race_date "http://www.nyrr.org/races-and-events/2015/nyrr-al-gordon-4-mile")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi

expected_title="For the Love of Queens 5K"
returned_title="$(get_race_title "https://nycruns.com/races/?race=for-the-love-of-queens-5k")"
if [ "$returned_title" != "$expected_title" ]
then
  echo "Test command failed! Got $returned_title, expected $expected_title"
  exit 2
fi

expected_date="february 14, 2015 9:00am"
returned_date="$(get_race_date "https://nycruns.com/races/?race=for-the-love-of-queens-5k")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi

expected_date="june 21, 2015 8:00"
returned_date="$(get_race_date "https://nycruns.com/races/?race=fathers-day-half-2015")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi

expected_title="NYCRUNS Father's Day Half Marathon"
returned_title="$(get_race_title "https://nycruns.com/races/?race=fathers-day-half-2015")"
if [ "$returned_title" != "$expected_title" ]
then
  echo "Test command failed! Got $returned_title, expected $expected_title"
  exit 2
fi



expected_date="february 22, 2015 8:00 am"
returned_date="$(get_race_date "https://nycruns.com/races/?race=nycruns-central-park-marathon-2015")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi





url="$1"

title="$(get_race_title "$url")"
date="$(get_race_date "$url")"

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
addrace.sh "$title" "$date" "$url" 