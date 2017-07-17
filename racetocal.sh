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

ACTIVE_TITLE_SELECTOR='h1[itemprop=name]'
ACTIVE_DATE_SELECTOR='meta[itemprop=startDate]'

GENERIC_TITLE_SELECTOR="meta[property=og:title]"
GENERIC_TITLE_SELECTOR2="title"
GENERIC_DATE_SELECTOR="div.field"
GENERIC_DATE_SELECTOR2="div.date"
GENERIC_DATE_SELECTOR3=".hero-subheading"
GENERIC_DATE_SELECTOR4="time.clrfix"
GENERIC_DATE_SELECTOR5="h3.tve_p_center"
GENERIC_DATE_SELECTOR6="meta[property=og:description]"

set -o nounset
set -o errexit
set -o pipefail

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

# Check argument
#
if [ ! "${1:-}" ]
then
  echo "Usage: $0 <URL>"
  exit 1
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

  if [ ! "$returned_title" ]
  then
    returned_title="$($CURL "$url" | $PUP "$GENERIC_TITLE_SELECTOR" attr{content})"
  fi

  if [ ! "$returned_title" ]
  then
    returned_title="$($CURL "$url" | $PUP "$GENERIC_TITLE_SELECTOR2" text{})"
  fi

  # Discard pipe and following text
  #
  returned_title="$(echo -n "$returned_title" | sed 's/ *|.*//' )"

  # Discard dash and following text
  #
  returned_title="$(echo -n "$returned_title" | sed 's/ * - .*//' )"

  # Trim trailing whitespace
  #
  returned_title="$(echo -n "$returned_title" | sed 's/[ 	]*$//' )"

  # Grab only first line
  #
  returned_title="$(echo -n "$returned_title" | head -1 )"

  # Remove leading "Home" text
  #
  returned_title="$(echo -n "$returned_title" | sed 's/Home [–-] //')"
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

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$GENERIC_DATE_SELECTOR" text{})"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$GENERIC_DATE_SELECTOR2" text{})"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$GENERIC_DATE_SELECTOR3" text{})"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$GENERIC_DATE_SELECTOR4" text{})"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$GENERIC_DATE_SELECTOR5" text{} | head -1)"
  fi

  # try active selector before generic selector 6, since generic selector 6 can catch a lot more
  #
  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$ACTIVE_DATE_SELECTOR" attr{content} | head -1)"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$GENERIC_DATE_SELECTOR6" attr{content})"
  fi



  returned_date="$(echo -n "$returned_date" | tr A-Z a-z | sed 's/start time://g' | sed 's/start\.//g')"
  returned_date="$(echo -n "$returned_date" | tr \\n \ )"
  returned_date="$(echo -n "$returned_date" | sed 's/.*will take place on //g')"
  returned_date="$(echo -n "$returned_date" | sed 's/half marathon starts at//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/full marathon starts at//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/race[- ]day.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/5k start//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ 5k:*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ 10k:*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ half:*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ 5 miler.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ - / /g')"
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	][ 	]*/ /g'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/;.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ *|.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/^[ 	]*//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	]*$//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ for both.*$//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ for the.*$//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ from / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ the / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ begins at / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ to .*//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/\. .*//'; )"
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

expected_date="saturday, february 20, 2016 8:00am"
returned_date="$(get_race_date "http://www.nyrr.org/races-and-events/2016/nyrr-al-gordon-4m")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi


# Test get_race_title and get_race_date
#
# Arguments: <url> <expected title> <expected date>
#
test_url() {
  url_to_test="$1"
  expected_title="$2"
  expected_date="$3"

  returned_title="$(get_race_title "$url_to_test")"
  returned_date="$(get_race_date "$url_to_test")"


  if [ "$returned_title" != "$expected_title" ]
  then
    echo "Test command failed! Got $returned_title, expected $expected_title"
    echo "Test URL: $url_to_test"
    exit 2
  fi

  if [ "$returned_date" != "$expected_date" ]
  then
    echo "Test command failed! Got $returned_date, expected $expected_date"
    echo "Test URL: $url_to_test"
    exit 2
  fi
}

url_to_test='http://www.active.com/new-york-ny/running/distance-running-races/stache-dash-nyc-5k-10k-2016?int='
expected_title="Stache Dash NYC 5K / 10K"
expected_date="2016-11-12t05:00:00"

test_url "$url_to_test" "$expected_title" "$expected_date"

url_to_test="https://nycruns.com/races/?race=queens-half"
expected_title="NYCRUNS Flushing Meadows Half Marathon & 5K"
expected_date="april 16, 2017 8:00am"

test_url "$url_to_test" "$expected_title" "$expected_date"

expected_title="ORLEN Warsaw Marathon"
expected_date="24 april 2016"
# url_to_test="https://www.orlenmarathon.pl/en/"
url_to_test="http://web.archive.org/web/20160321034209/http://www.orlenmarathon.pl/en/"

test_url "$url_to_test" "$expected_title" "$expected_date"

expected_title="Virgin Money London Marathon"
expected_date="22 april 2018"
url_to_test="https://www.virginmoneylondonmarathon.com/en-gb/"

test_url "$url_to_test" "$expected_title" "$expected_date"


expected_title="Yosemite Half Marathon"
expected_date="may 12, 2018"
url_to_test="http://www.yosemitehalfmarathon.com/"

test_url "$url_to_test" "$expected_title" "$expected_date"



expected_date="march 18, 2018"
returned_date="$(get_race_date "https://nycruns.com/races/?race=nycruns-spring-fling-5k-10k")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi

expected_date="april 22, 2017 8:00am"
returned_date="$(get_race_date "https://nycruns.com/races/?race=nycruns-prospect-park-10k")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi



expected_title="Run the River 5K"
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
