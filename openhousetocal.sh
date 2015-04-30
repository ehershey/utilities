#!/bin/bash
#
# Add open house to calendar by Zillow listing URL
#
ZILLOW_TITLE_SELECTOR="h1"
ZILLOW_DATE_SELECTOR="span[itemprop=\"date\"]"
ZILLOW_PRICE_SELECTOR="div.main-row"
ZILLOW_DESCRIPTION_SELECTOR="span.addr_bbs"
STREETEASY_TITLE_SELECTOR=".building-title"
STREETEASY_DATE_SELECTOR="span.clearfix"
STREETEASY_PRICE_SELECTOR=""

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

  # Trim leading comma and whitespace
  #
  returned_title="$(echo -n "$returned_title" | sed 's/^[ 	]*//'; )"

  echo "$returned_title"
}

get_date() {
  url="$1"
  returned_date="$($CURL "$url" | $PUP "$ZILLOW_DATE_SELECTOR" text{})"
  if [[ ! "$returned_date" ]]
  then
    returned_date="$($CURL "$url" | $PUP "$STREETEASY_DATE_SELECTOR" text{})"
  fi
  returned_date="$(echo -n "$returned_date" | tr \\n \ )"
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	][ 	]*/ /g'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/;.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/).*/)/g')"
  returned_date="$(echo -n "$returned_date" | sed 's/^[ 	]*//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	]*$//'; )"
  echo "$returned_date"
}


get_description() {
  url="$1"
  returned_description="$($CURL "$url" | $PUP "$ZILLOW_DESCRIPTION_SELECTOR" text{})"
  returned_description="$(echo -n "$returned_description" |  tr \\n , | sed 's/,/, /g')"
  echo "$returned_description"
}

get_price() {
  url="$1"
  returned_price="$($CURL "$url" | $PUP "$ZILLOW_PRICE_SELECTOR" text{})"
  returned_price="$(echo -n "$returned_price" | tr \\n \ )"
  returned_price="$(echo -n "$returned_price" | sed 's/^[ 	]*//'; )"
  returned_price="$(echo -n "$returned_price" | sed 's/[ 	]*$//'; )"
  echo "$returned_price"
}


# Validate selectors and scraping logic
#
expected_title="270 Jay St APT 2A Brooklyn, NY 11201"
returned_title="$(get_address "http://www.zillow.com/homedetails/270-Jay-St-APT-2A-Brooklyn-NY-11201/79724917_zpid/")"
if [ "$returned_title" != "$expected_title" ]
then
  echo "Test command failed (get_title)! Got >$returned_title<, expected >$expected_title<"
  exit 2
fi

#expected_date="3/8 12pm-1:30pm"
#returned_date="$(get_date "http://www.zillow.com/homedetails/270-Jay-St-APT-2A-Brooklyn-NY-11201/79724917_zpid/")"
#if [ "$returned_date" != "$expected_date" ]
#then
  #echo "Test command failed! Got $returned_date, expected $expected_date"
  #exit 2
#fi

expected_description="Studio, 1 bath, 468 sqft"
returned_description="$(get_description "http://www.zillow.com/homedetails/225-Adams-St-APT-14E-Brooklyn-NY-11201/2111123696_zpid/")"
if [ "$returned_description" != "$expected_description" ]
then
  echo "Test command failed (get_description)! Got $returned_description, expected $expected_description"
  exit 2
fi

expected_price='$315,000'
returned_price="$(get_price "http://www.zillow.com/homedetails/225-Adams-St-APT-14E-Brooklyn-NY-11201/2111123696_zpid/")"
if [ "$returned_price" != "$expected_price" ]
then
  echo "Test command failed (get_price)! Got $returned_price, expected $expected_price"
  exit 2
fi
#expected_date="Sun, Mar 15 (1:00 PM - 3:00 PM)"
#returned_date="$(get_date "http://streeteasy.com/building/concord-village-235-adams-street-brooklyn/7b")"
#if [ "$returned_date" != "$expected_date" ]
#then
  #echo "Test command failed! Got $returned_date, expected $expected_date"
  #exit 2
#fi

#expected_address="235 Adams Street #7B"
#returned_address="$(get_address "http://streeteasy.com/building/concord-village-235-adams-street-brooklyn/7b")"
#if [ "$returned_address" != "$expected_address" ]
#then
  #echo "Test command failed! Got $returned_address, expected $expected_address"
  #exit 2
#fi


url="$1"

location="$(get_address "$url" | perl -p -e 's/ apt \S+//i')"
title="$(get_address "$url" | head -1 | perl -p -e 's/ *brooklyn.*//i')"
date="$(get_date "$url")"
description="$(get_description "$url")"
price="$(get_price "$url")"

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
daymonth=${daymonth% (*}
fulltime=${date#* }
fulltime="$(echo "$fulltime" | sed 's/.*(//')"
fulltime="$(echo "$fulltime" | tr -d \(\))"
starttime=${fulltime%-*}
endtime=${fulltime#*-}

startunixtime=$(perl -MDate::Parse -e "print str2time(\"$daymonth $starttime\"),\"\n\"" )
endunixtime=$(perl -MDate::Parse -e "print str2time(\"$daymonth $endtime\"),\"\n\"" )

duration=$(expr \( $endunixtime - $startunixtime \) / 60)

if ! echo "$duration" | grep -xq '^[0-9][0-9]*'
then
  echo "invalid duration: >$duration<"
  exit 5
fi


addopenhouse.sh "$title" "$daymonth $starttime" "$description$price$url" "$duration" "$location"
