#!/bin/bash
#
# Add Race to calendar
#
# autoupdate_version = 21
#
NYRR_TITLE_SELECTOR="h2.title"
NYRR_DATE_SELECTOR="p.full-width span"

NYCRUNS_TITLE_SELECTOR=".race-display-name"
NYCRUNS_TITLE_SELECTOR2="h1._title"
NYCRUNS_DATE_SELECTOR=".race-display-date"
NYCRUNS_DATE_SELECTOR2="._date , ._subtitle"
NYCRUNS_ADDRESS_SELECTOR=".race-display-address"

RNR_DATE_SELECTOR="h2:contains(\"General Info\") + p + p"
RNR_TITLE_SELECTOR="h2:contains(\"General Info\") + p"

EVENTBRITE_TITLE_SELECTOR="span.summary"
EVENTBRITE_DATE_SELECTOR="span.dtstart"

ACTIVE_TITLE_SELECTOR='h1[itemprop=name]'
ACTIVE_DATE_SELECTOR='meta[itemprop=startDate]'

TRANSALT_DATE_SELECTOR='time'

GENERIC_TITLE_SELECTOR="meta[property=og:title]"
GENERIC_TITLE_SELECTOR2="title"

GENERIC_TITLE_SELECTORS="
p.Style22
"
GENERIC_DATE_SELECTORS="
.race-date
div.race_detail-meta_list__value
div.event-date
p.text-align-center
meta[property=event:start_time]
div.timer
h2.date
h4.mb32
p.Style23
div.wpb_wrapper\ p:parent-of(strong:contains(\"Date\"))
div.race_detail-result_summary__item__title
"
GENERIC_DATE_SELECTOR="div.field"
GENERIC_DATE_SELECTOR2="div.date"
GENERIC_DATE_SELECTOR3=".hero-subheading"
GENERIC_DATE_SELECTOR4="time.clrfix"
GENERIC_DATE_SELECTOR5="h3.tve_p_center"
GENERIC_DATE_SELECTOR6="h1"
GENERIC_DATE_SELECTOR7="meta[property=og:description]"
GENERIC_DATE_SELECTOR8="section.fullheader div.container div.message p"

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

# Make sure gsed is available
#
if ! which gsed &>/dev/null
then
  echo "gsed utility required (from gnu-sed homebrew package)"
  exit 3
fi


# Check argument
#
if [ ! "${1:-}" -a "$(basename "$0")" == "racetocal.sh" ]
then
  echo "Usage: $0 <URL> [ <DATE> [ <title> ] ]"
  exit 1
fi

if [ "${2:-}" ]
then
  arg_date="$2"
else
  arg_date=""
fi

if [ "${3:-}" ]
then
  arg_title="$3"
else
  arg_title=""
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
    returned_title="$($CURL "$url" | $PUP "$NYCRUNS_TITLE_SELECTOR2" text{})"
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

  for title_selector in $GENERIC_TITLE_SELECTORS
  do
    if [ ! "$returned_title" ]
    then
       returned_title="$($CURL "$url" | $PUP "$title_selector" attr{content})"
    fi
    if [ ! "$returned_title" ]
    then
       returned_title="$($CURL "$url" | $PUP "$title_selector" text{})"
    fi
    if [ ! "$returned_title" ]
    then
      returned_title="$($CURL "$url" | $PUP "$title_selector" attr{data-event-title} | head -1)" # loch ness marathon
    fi
  done


  # Discard pipe and preceding text
  #
  returned_title="$(echo -n "$returned_title" | sed 's/.*| *//' )"

  # Discard arrow char and following text ("Â" from archive.org)
  #
  returned_title="$(echo -n "$returned_title" | sed 's/ *[Â»].*//' )"

  # Discard dash and following text
  #
  returned_title="$(echo -n "$returned_title" | sed 's/ * - .*//' )"

  # Trim trailing whitespace
  #
  returned_title="$(echo -n "$returned_title" | sed 's/[ 	]*$//' )"

  # Trim leading whitespace
  #
  returned_title="$(echo -n "$returned_title" | sed 's/^[ 	]*//' )"

  # Grab only first line
  #
  returned_title="$(echo -n "$returned_title" | grep . | head -1 )"

  # Remove leading "Home" text (â€“ from archive.org)
  #
  returned_title="$(echo -n "$returned_title" | sed 's/Home [â€“–-]* //')"

  # Remove leading "the" text
  #
  returned_title="$(echo -n "$returned_title" | gsed 's/^the //i')"

  # Remove leading "Nth annual" text
  #
  returned_title="$(echo -n "$returned_title" | gsed 's/[0-9][0-9]*th annual //i')"

  echo "$returned_title"
}

get_race_date() {
  url="$1"
  returned_date="$($CURL "$url" | $PUP "$NYRR_DATE_SELECTOR" text{})"
  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$NYCRUNS_DATE_SELECTOR" text{})"
  fi

  for date_selector in $GENERIC_DATE_SELECTORS
  do
    if [ ! "$returned_date" ]
    then
      returned_date="$($CURL "$url" | $PUP "$date_selector" attr{content} | grep -v Finishers)"
    fi
    if [ ! "$returned_date" ]
    then
       returned_date="$($CURL "$url" | $PUP "$date_selector" text{} | grep -v Finishers)"
    fi
    if [ ! "$returned_date" ]
    then
      returned_date="$($CURL "$url" | $PUP "$date_selector" attr{data-event-date} | head -1)" # loch ness marathon
    fi
  done

  # Grab only first two lines
  #
  returned_date="$(echo -n "$returned_date" | grep . | head -3 )"


  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$NYCRUNS_DATE_SELECTOR2" text{})"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$RNR_DATE_SELECTOR" text{})"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$ACTIVE_DATE_SELECTOR" attr{content} | head -1)"
  fi


  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$EVENTBRITE_DATE_SELECTOR" text{})"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$GENERIC_DATE_SELECTOR" text{})"
  fi

  for date_selector in $GENERIC_DATE_SELECTORS
  do
    if [ ! "$returned_date" ]
    then
       returned_date="$($CURL "$url" | $PUP "$date_selector" attr{content} | tail -1)"
    fi
    if [ ! "$returned_date" ]
    then
       returned_date="$($CURL "$url" | $PUP "$date_selector" text{} | tail -1)"
    fi
  done

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
    returned_date="$($CURL "$url" | $PUP "$GENERIC_DATE_SELECTOR5" text{} | tr -d \\n)"
  fi

  # try specialized selectors before generic selector 6, since generic selector 6 can catch a lot more
  #
  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$TRANSALT_DATE_SELECTOR" text{})"
  fi


  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$GENERIC_DATE_SELECTOR6" attr{content})"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$GENERIC_DATE_SELECTOR7" text{} | head -1)"
  fi

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$GENERIC_DATE_SELECTOR8" text{} | head -1)"
  fi




  returned_date="$(echo -n "$returned_date" | tr A-Z a-z | sed 's/start time://g' | sed 's/start\.//g')"
  returned_date="$(echo -n "$returned_date" | tr '[:blank:]'\\n \ )"
  returned_date="$(echo -n "$returned_date" | sed 's/.*will take place on //g')"
  returned_date="$(echo -n "$returned_date" | sed 's/half marathon starts at//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/full marathon starts at//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/race[- ]day.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/5k start//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ 5k:*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ 10k:*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ half:*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ 5 miler.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ - [0-9][0-9]*:[0-9][0-9] [ap]m//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	][ 	]*/ /g'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/;.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/ *|.*//g')"
  returned_date="$(echo -n "$returned_date" | sed 's/^[ 	]*//'; )"

  # Berlin date has a lot of space between title and date
  #
  returned_date="$(echo -n "$returned_date" | sed 's/.*        *on //'; )"

  # Montauk ride also has weird spaces - september 1 4 , 2019
  #
  returned_date="$(echo -n "$returned_date" |  gsed 's/\([a-z][a-z]*\) \([0-9]\) \([0-9]\) , \(20[0-9][0-9]\)/\1 \2\3, \4/i' )"



  # includes weird whitespace chars - should replace with named character class
  #
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	  ]*$//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ for both.*$//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ for the.*$//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ from / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ the / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ begins at / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ to .*//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/\. .*//'; )"

  # run the river 5k eventbrite 2018 has lots of space and random words in otherwise good date info
  #
  # e.g. "sat, october 27, 2018 10:00 am"
  #
  returned_date="$(echo -n "$returned_date" | sed 's/.*[^a-z]\([a-z][a-z][a-z]*, [a-z][a-z][a-z]* [0-9][0-9]*, [0-9][0-9][0-9][0-9] [0-9][0-9]*:[0-9][0-9]* [ap]m\).*/\1/' )"

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
    echo "Test command failed! Got:"
    echo ">$returned_title<"
    echo "expected:"
    echo ">$expected_title<"
    echo "Test URL: $url_to_test"
    exit 2
  fi

  if [ "$returned_date" != "$expected_date" ]
  then
    echo "Test command failed! Got:"
    echo ">$returned_date<"
    echo "expected:"
    echo ">$expected_date<"
    echo "Test URL: $url_to_test"
    exit 2
  fi
}

# Validate selectors and scraping logic
#

expected_title="NYRR Grete's Great Gallop 10K"
expected_date="saturday, october 05 2019"
#october 5, 2019 8:00 am"
url_to_test="https://www.nyrr.org/races/nyrrgrete39sgreatgallop10k"
test_url "$url_to_test" "$expected_title" "$expected_date"

expected_title="NYRR Al Gordon 4M"
expected_date="saturday, february 20, 2016 8:00am"
#url_to_test="http://www.nyrr.org/races-and-events/2015/nyrr-al-gordon-4-mile"
url_to_test="http://web.archive.org/web/20170624014508/http://www.nyrr.org/races-and-events/2016/nyrr-al-gordon-4m"
test_url "$url_to_test" "$expected_title" "$expected_date"

expected_date="saturday, february 20, 2016 8:00am"
expected_title="NYRR Al Gordon 4M"
#url_to_test="http://www.nyrr.org/races-and-events/2016/nyrr-al-gordon-4m"
url_to_test="http://web.archive.org/web/20170624014508/http://www.nyrr.org/races-and-events/2016/nyrr-al-gordon-4m"
test_url "$url_to_test" "$expected_title" "$expected_date"



#url_to_test="https://nycruns.com/races/?race=paine-to-pain-trail-half-marathon-2018"
#expected_title="Paine to Pain Trail Half Marathon"
#expected_date="sunday, october 7, 2018 9:00 am"
#
#test_url "$url_to_test" "$expected_title" "$expected_date"

expected_title="ORLEN Warsaw Marathon"
expected_date="24 april 2016"
# url_to_test="https://www.orlenmarathon.pl/en/"
url_to_test="http://web.archive.org/web/20160321034209/http://www.orlenmarathon.pl/en/"

test_url "$url_to_test" "$expected_title" "$expected_date"

expected_title="Virgin Money London Marathon"
expected_date="22 april 2018"
#url_to_test="https://www.virginmoneylondonmarathon.com/en-gb/"
url_to_test="https://web.archive.org/web/20180401061548/https://www.virginmoneylondonmarathon.com/en-gb/"

test_url "$url_to_test" "$expected_title" "$expected_date"


#expected_title="Yosemite Half Marathon (Direct)"
expected_title="Yosemite Half Marathon"
expected_date="may 12th, 2018"
#url_to_test="http://www.yosemitehalfmarathon.com/"
url_to_test="https://web.archive.org/web/20171022082812/https://vacationraces.com/half-marathons/yosemite/"

test_url "$url_to_test" "$expected_title" "$expected_date"



#expected_title="NYCRUNS Spring Fling 5K & 10K"
#expected_date="saturday, march 17, 2018 8:30am"
#url_to_test="https://nycruns.com/races/?race=nycruns-spring-fling-5k-10k"
#
#test_url "$url_to_test" "$expected_title" "$expected_date"


expected_title="Run the River 5K"
#expected_date="2015-10-24t08:30:00-04:00"
expected_date="2015-10-24t10:00:00-04:00"
#url_to_test="http://www.eventbrite.com/e/run-the-river-5k-icahn-stadiumrandalls-island-park-registration-17885348559?nomo=1"
url_to_test="http://web.archive.org/web/20151002012505/http://www.eventbrite.com/e/run-the-river-5k-icahn-stadiumrandalls-island-park-registration-17885348559?nomo=1"
test_url "$url_to_test" "$expected_title" "$expected_date"

expected_title="Run the River 5K"
#expected_date="sat, october 27, 2018 10:00 am"
expected_date="2018-10-27t10:00:00-04:00"
url_to_test="https://www.eventbrite.com/e/run-the-river-5k-registration-45356619871?bbemailid=9327519&bblinkid=110100196&bbejrid=712167945"
test_url "$url_to_test" "$expected_title" "$expected_date"

url="http://web.archive.org/web/20190413234301/https://nyccentury.org/"
date="sunday, september 9 6:00 am"
title="NYC Century"
test_url "$url" "$title" "$date"

test_url https://web.archive.org/web/20190118081846/http://www.ridetomontauk.com/ 'Ride to Montauk' 'september 14, 2019'

test_url http://web.archive.org/web/20190816170055/https://nytri.org/events/rockaway-beach-tri-duathlon/ 'Rockaway Beach Tri/Duathlon' 'date: sunday, september 22, 2019'

test_url http://web.archive.org/web/20190923170820/https://runsignup.com/Race/NY/Brooklyn/PPTCTurkeyTrot?remMeAttempt=  '2019 PPTC Turkey Trot' 'thu november 28 2019'

if [ "$(basename "$0")" == "racetocal.sh" ]
then
  url="$1"

  if [ "$arg_title" ]
  then
    title="$arg_title"
  else
    title="$(get_race_title "$url")"
  fi

  if [ "$arg_date" ]
  then
    date="$arg_date"
  else
    date="$(get_race_date "$url")"
  fi
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
  echo "title=\"$title\""
  echo "date=\"$date\""
  echo "url=\"$url\""
  echo "address=\"$address\""
  set -o xtrace
  addrace.sh "$title" "$date" "$url" "" "$address"
fi
