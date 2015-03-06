#!/bin/bash
#
# Add open house to calendar by Zillow listing URL
#
ZILLOW_TITLE_SELECTOR="h1"
ZILLOW_DATE_SELECTOR="span[itemprop=\"date\"]"



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


get_address() {
  url="$1"
  returned_title="$($CURL "$url" | $PUP "$ZILLOW_TITLE_SELECTOR" text{})"

  # Trim trailing comma and whitespace
  #
  returned_title="$(echo -n "$returned_title" | sed 's/[, ]*$//g' )"

  # Convert to single line
  #
  returned_title="$(echo "$returned_title" | tr \\n \ )"

  # Trim trailing comma and whitespace
  #
  returned_title="$(echo -n "$returned_title" | sed 's/[, ]*$//g' )"

  echo "$returned_title"
}

get_date() {
  url="$1"
  returned_date="$($CURL "$url" | $PUP "$ZILLOW_DATE_SELECTOR" text{})" 
  returned_date="$(echo -n "$returned_date" | tr \\n \ )"
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	][ 	]*/ /g'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/;.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/^[ 	]*//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	]*$//'; )"
  echo "$returned_date"
}

# Validate selectors and scraping logic
#
expected_title="270 Jay St APT 2A Brooklyn, NY 11201"
returned_title="$(get_address "http://www.zillow.com/homedetails/270-Jay-St-APT-2A-Brooklyn-NY-11201/79724917_zpid/")"
if [ "$returned_title" != "$expected_title" ]
then
  echo "Test command failed! Got >$returned_title<, expected >$expected_title<"
  exit 2
fi

expected_date="3/8 12pm-1:30pm"
returned_date="$(get_date "http://www.zillow.com/homedetails/270-Jay-St-APT-2A-Brooklyn-NY-11201/79724917_zpid/")"
if [ "$returned_date" != "$expected_date" ]
then
  echo "Test command failed! Got $returned_date, expected $expected_date"
  exit 2
fi

url="$1"

location="$(get_address "$url" | perl -p -e 's/ apt \S+//i')"
title="$(echo "$location" | head -1)"
date="$(get_date "$url")"

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

title="Open house - $title"
daymonth=${date% *}
fulltime=${date#* }
starttime=${fulltime%-*}
endtime=${fulltime#*-}

startunixtime=$(perl -MDate::Parse -e "print str2time(\"$daymonth $starttime\"),\"\n\"" )
endunixtime=$(perl -MDate::Parse -e "print str2time(\"$daymonth $endtime\"),\"\n\"" )

duration=$(expr \( $endunixtime - $startunixtime \) / 60)

addopenhouse.sh "$title" "$daymonth $starttime" "$url" "$duration" "$location"
