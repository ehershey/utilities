#!/bin/bash
#
# Add Race to calendar
#
# autoupdate_version = 136
#
NYRR_TITLE_SELECTOR="h2.title"
NYRR_DATE_SELECTOR="p.full-width span"

NYCRUNS_TITLE_SELECTOR=".race-display-name"
NYCRUNS_TITLE_SELECTOR2="h1._title"
NYCRUNS_DATE_SELECTOR=".race-display-date"
NYCRUNS_DATE_SELECTOR2="._date , ._subtitle"

GENERIC_LOCATION_SELECTOR='li:parent-of(h2:contains("Location")) div'
GENERIC_LOCATION_SELECTORS="
.race-display-address
span.race-location
._address
"

RNR_DATE_SELECTOR="h2:contains(\"General Info\") + p + p"
RNR_TITLE_SELECTOR="h2:contains(\"General Info\") + p"

EVENTBRITE_TITLE_SELECTOR="span.summary"
EVENTBRITE_DATE_SELECTOR="span.dtstart"

ACTIVE_TITLE_SELECTOR='h1[itemprop=name]'
ACTIVE_DATE_SELECTOR='meta[itemprop=startDate]'

TRANSALT_DATE_SELECTOR='time'

GENERIC_TITLE_SELECTORS='
div\ div\ div.sqs-block-content\ h1
meta[property=og:title]
title
p.Style22
'

GENERIC_DATE_SELECTORS="
.event-date
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
.textwidget
"
GENERIC_DATE_SELECTOR="div.field"
GENERIC_DATE_SELECTOR2="div.date"
GENERIC_DATE_SELECTOR3=".hero-subheading"
GENERIC_DATE_SELECTOR4="time.clrfix"
GENERIC_DATE_SELECTOR5="h3.tve_p_center"
GENERIC_DATE_SELECTOR6="h1"
GENERIC_DATE_SELECTOR7="meta[property=og:description]"
GENERIC_DATE_SELECTOR8="section.fullheader div.container div.message p"

CACHE_TIMEOUT_SECONDS=2592000 # 30 days

# skip tests if this version of script has been tested in the last 30 days
#
if which md5 >/dev/null 2>&1
then
  md5=md5
elif which md5sum >/dev/null 2>&1
then
  md5=md5sum
fi
script_hash=$($md5 < "$BASH_SOURCE")
test_success_timestamp_file="/tmp/test_success_timestamp_${script_hash}"
if [ -e "$test_success_timestamp_file" ]
then
  test_success_timestamp=$(cat $test_success_timestamp_file)
  now=$(date +%s)
  test_success_age=$(expr $now - $test_success_timestamp)
  if [ "$test_success_age" -lt 2592000 ]
  then
    SKIP_TESTS=1
  fi
fi


if [ "$(basename "$0")" == "racetocal.sh" ]
then
  set -o nounset
  set -o errexit
  set -o pipefail
fi

# Use cache_get if available, else curl
#
if which cache_get &>/dev/null
then
  CURL="cache_get $CACHE_TIMEOUT_SECONDS"
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
  echo "Usage: $0 <URL> [ <DATE> [ <title> [ <location> ] ] ]"
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

if [ "${4:-}" ]
then
  arg_location="$4"
else
  arg_location=""
fi


get_race_title() {
  echo -n .>&2
  url="$1"
  returned_title="$($CURL "$url" | $PUP "$NYRR_TITLE_SELECTOR" text{})"
  returned_title_pattern="$NYRR_TITLE_SELECTOR text{}"
  if [ ! "$returned_title" ]
  then
    returned_title="$($CURL "$url" | $PUP "$NYCRUNS_TITLE_SELECTOR" text{})"
    returned_title_pattern="$NYCRUNS_TITLE_SELECTOR text{}"
  fi

  if [ ! "$returned_title" ]
  then
    returned_title="$($CURL "$url" | $PUP "$NYCRUNS_TITLE_SELECTOR2" text{})"
    returned_title_pattern="$NYCRUNS_TITLE_SELECTOR2 text{}"
  fi

  if [ ! "$returned_title" ]
  then
    returned_title="$($CURL "$url" | $PUP "$RNR_TITLE_SELECTOR" text{})"
    returned_title_pattern="$RNR_TITLE_SELECTOR text{}"
  fi

  if [ ! "$returned_title" ]
  then
    returned_title="$($CURL "$url" | $PUP "$EVENTBRITE_TITLE_SELECTOR" text{})"
    returned_title_pattern="$EVENTBRITE_TITLE_SELECTOR text{}"
  fi

  while read title_selector
  do
    if [ ! "$title_selector" ]
    then
      continue
    fi
    if [ ! "$returned_title" ]
    then
       returned_title="$($CURL "$url" | $PUP "$title_selector" attr{content})"
       returned_title_pattern="$title_selector attr{content}"
    fi
    if [ ! "$returned_title" ]
    then
       returned_title="$($CURL "$url" | $PUP "$title_selector" text{})"
       returned_title_pattern="$title_selector text{}"
    fi
    if [ ! "$returned_title" ]
    then
      returned_title="$($CURL "$url" | $PUP "$title_selector" attr{data-event-title} | head -1)" # loch ness marathon
      returned_title_pattern="$title_selector attr{data-event-title} | head -1"
    fi
  done <<< "$GENERIC_TITLE_SELECTORS"


  # Discard pipe and text afterwards
  ## Discard pipe and preceding text
  #
  # inverted 20200917 for warsaw marathon
  # Undid 20200928 for nyc century
  #
  returned_title="$(echo -n "$returned_title" | sed 's/.*| *//' )"
  #returned_title="$(echo -n "$returned_title" | sed 's/ *|.*//' )"

  # Discard "- ATRA" for trailrunner.com
  #
  returned_title="$(echo -n "$returned_title" | gsed 's/ â ATRA$//' )"

  # Discard "â.*" and stuff from nycruns.com
  #
  returned_title="$(echo -n "$returned_title" | gsed 's/ *â.*NYCRUNS$//' )"
  returned_title="$(echo -n "$returned_title" | gsed 's/  ¿ NYCRUNS$//' )"
  returned_title="$(echo -n "$returned_title" | gsed 's/ – NYCRUNS$//' )"

  # Remove leading "Home" text (Ã¢â¬â from archive.org)
  #
  returned_title="$(echo -n "$returned_title" | sed 's/Home [Ã¢â¬ââ-]* //')"

  # Discard arrow char and following text ("Ã" from archive.org)
  #
  returned_title="$(echo -n "$returned_title" | sed 's/ *[ÃÂ»].*//' )"

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

  # Remove leading "the" text
  #
  returned_title="$(echo -n "$returned_title" | gsed 's/^the //i')"

  # Remove leading "Nth annual" text
  #
  returned_title="$(echo -n "$returned_title" | gsed 's/[0-9][0-9]*th annual //i')"

  # Remove extra bs - https://runsignup.com/Race/CO/HighlandsRanch/BackCountryHalfMarathon
  #
  returned_title="$(echo -n "$returned_title" | gsed 's/: Presented By.*//i')"

  # Remove year from beginning of title - also https://runsignup.com/Race/CO/HighlandsRanch/BackCountryHalfMarathon
  #
  returned_title="$(echo -n "$returned_title" | gsed "s/^20[0-9][0-9]  *//")"

  echo "$returned_title"
}

get_race_date() {
  echo -n .>&2
  url="$1"
  returned_date="$($CURL "$url" | $PUP "$NYRR_DATE_SELECTOR" text{})"
  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | $PUP "$NYCRUNS_DATE_SELECTOR" text{})"
  fi

  # [ernie@eahimac4 ~]$ cache_Get 86400 'https://ultrasignup.com/register.aspx?did=79440' | grep start.: | grep -v \< | cut -f4 -d\"

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | grep \"start\": | grep -v \< | grep -v has_external_ticketing_properties | cut -f4 -d\")" # ultrasignup.com
    # has_external_ticketing_properties is from https://www.eventbrite.com/e/run-the-river-5k-registration-45356619871?bbemailid=9327519&bblinkid=110100196&bbejrid=712167945
  fi

  # [ernie@eahimac4 utilities[master*]]$ cache_get 86400 https://pptc.org/50-miler | grep -i 'race day is' | sed 's/.*Race day is \([^.]*\)\..*$/\1/'

  if [ ! "$returned_date" ]
  then
    returned_date="$($CURL "$url" | grep -i 'race day is' | sed 's/.*Race day is \([^.]*\)\..*$/\1/' )" # pptc.org
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
  returned_date="$(echo -n "$returned_date" | sed 's/ - [0-9][0-9]*:*[0-9]* [ap]m//g')"
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
  returned_date="$(echo -n "$returned_date" | sed 's/[ 	Â  ]*$//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ for both.*$//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ for the.*$//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ from / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ the / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ begins at / /'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/waves starting at //'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/ to .*//'; )"
  returned_date="$(echo -n "$returned_date" | sed 's/\. .*//'; )"

  # run the river 5k eventbrite 2018 has lots of space and random words in otherwise good date info
  #
  # e.g. "sat, october 27, 2018 10:00 am"
  #
  returned_date="$(echo -n "$returned_date" | sed 's/.*[^a-z]\([a-z][a-z][a-z]*, [a-z][a-z][a-z]* [0-9][0-9]*, [0-9][0-9][0-9][0-9] [0-9][0-9]*:[0-9][0-9]* [ap]m\).*/\1/' )"

  echo "$returned_date"
}

get_race_url() {
  url="$1"
  returned_url="$($CURL "$url" | $PUP .websiteitem attr{href})"

  if [ ! "$returned_url" ]
  then
    returned_url="$url"
  fi
  echo "$returned_url"
}

get_race_location() {
  url="$1"
  #returned_location="$($CURL "$url" | $PUP "$GENERIC_LOCATION_SELECTOR" attr{content})"
  returned_location="$($CURL "$url" | $PUP "$GENERIC_LOCATION_SELECTOR" text{} | grep . | head -1)"

  for location_selector in $GENERIC_LOCATION_SELECTORS
  do
    if [ ! "$returned_location" ]
    then
       returned_location="$($CURL "$url" | $PUP "$location_selector" attr{content})"
    fi
    if [ ! "$returned_location" ]
    then
       returned_location="$($CURL "$url" | $PUP "$location_selector" text{})"
    fi
  done

  # [ernie@eahimac4 ~]$ cache_Get 86400 'https://ultrasignup.com/register.aspx?did=79440' | grep start.: | grep -v \< | cut -f4 -d\"
  # February 6, 2021 07:30:00
  # [ernie@eahimac4 ~]$ cache_Get 86400 'https://ultrasignup.com/register.aspx?did=79440' | grep location.: | grep -v \< | cut -f4 -d\"
  # Bryceville, FL
  # [ernie@eahimac4 ~]$

  if [ ! "$returned_location" ]
  then
    returned_location="$($CURL "$url" | grep location.: | grep -v \< | cut -f4 -d\")"
  fi


  # remove "Directions" text ala http://web.archive.org/web/20201026221754/https://runsignup.com/Race/CO/HighlandsRanch/BackCountryHalfMarathon
  #
  returned_location="$(echo -n "$returned_location" | grep -v Directions)"

  # Trim trailing whitespace
  #
  returned_location="$(echo -n "$returned_location" | sed 's/[ 	]*$//' )"

  # Convert whitespace to spaces
  #
  returned_location="$(echo -n "$returned_location" | tr \\n \ )"
  returned_location="$(echo -n "$returned_location" | sed 's/[	 ][ 	]*/ /g' )"


  # Grab only last line
  #
  returned_location="$(echo -n "$returned_location" | tail -1 )"

  returned_location="$(echo -n "$returned_location" | sed 's/^[ 	]*//'; )"
  echo "$returned_location"
}


# Test get_race_title and get_race_date
#
# Arguments: <url> <expected title> <expected date> [ <expected pattern> ] [ <expected location> ] [ <expected url> ]
#
test_url() {
  if [ "${SKIP_TESTS:-}" ]
  then
    return
  fi

  echo -n .>&2
  url_to_test="$1"
  expected_title="$2"
  expected_date="$3"
  expected_location="${5:-}"
  pattern_comments="${4:-}"
  expected_url="${6:-}"

  # not working
  returned_title_pattern=""

  returned_title="$(get_race_title "$url_to_test")"
  returned_date="$(get_race_date "$url_to_test")"
  returned_location="$(get_race_location "$url_to_test")"
  returned_url="$(get_race_url "$url_to_test")"


  if [ "$returned_title" != "$expected_title" ]
  then
    echo # after progress no-newline echos
    echo "Test command failed! Got:"
    echo ">$returned_title<"
    echo "expected:"
    echo ">$expected_title<"
    echo "Test URL: $url_to_test"
    if [ "$pattern_comments" ]
    then
        echo "Pattern comments (by URL so may not cover title matches): $pattern_comments"
    fi
    if [ "$returned_title_pattern" ]
    then
        echo "Matching pattern: $returned_title_pattern"
    fi

    exit 2
  fi

  if [ "$returned_date" != "$expected_date" ]
  then
    echo # after progress no-newline echos
    echo "Test command failed! Got:"
    echo ">$returned_date<"
    echo "expected:"
    echo ">$expected_date<"
    echo "Test URL: $url_to_test"
    if [ "$pattern_comments" ]
      then
        echo "Pattern comments (by URL so may not cover date matches): $pattern_comments"
    fi
    exit 2
  fi

  if [ "$expected_location" -a "$returned_location" != "$expected_location" ]
  then
    echo # after progress no-newline echos
    echo "Test command failed! Got:"
    echo ">$returned_location<"
    echo "expected:"
    echo ">$expected_location<"
    echo "Test URL: $url_to_test"
    if [ "$pattern_comments" ]
      then
        echo "Pattern comments (by URL so may not cover location matches): $pattern_comments"
    fi
    exit 2
  fi


  if [ "$expected_url" -a "$returned_url" != "$expected_url" ]
  then
    echo # after progress no-newline echos
    echo "Test command failed! Got:"
    echo ">$returned_url<"
    echo "expected:"
    echo ">$expected_url<"
    echo "Test URL: $url_to_test"
    if [ "$pattern_comments" ]
      then
        echo "Pattern comments (by URL so may not cover location matches): $pattern_comments"
    fi
    exit 2
  fi


}

# Validate selectors and scraping logic
#


test_url https://nycruns.com/race/nycruns-winter-classic-4-miler 'NYCRUNS Winter Classic 4 Miler' 'sunday, january 10, 2021' '' 'Central Park 72nd Street New York, NY'

test_url 'https://nycruns.com/race/central-park-half--marathon' 'NYCRUNS Central Park Half Marathon' 'sunday, february 28, 2021 7 am'

expected_title="NYRR Grete's Great Gallop 10K"
expected_date="saturday, october 05 2019"
#october 5, 2019 8:00 am"
#url_to_test="https://www.nyrr.org/races/nyrrgrete39sgreatgallop10k"
url_to_test="http://web.archive.org/web/20191104215923/https://www.nyrr.org/races/nyrrgrete39sgreatgallop10k"
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

#expected_title="ORLEN Warsaw Marathon"
#expected_date="24 april 2016"
## url_to_test="https://www.orlenmarathon.pl/en/"
#url_to_test="http://web.archive.org/web/20160321034209/http://www.orlenmarathon.pl/en/"

#test_url "$url_to_test" "$expected_title" "$expected_date"

test_url "https://web.archive.org/web/20180401061548/https://www.virginmoneylondonmarathon.com/en-gb/" "Virgin Money London Marathon" "22 april 2018" "title:meta[name=description] attr{content}"


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

test_url "https://web.archive.org/web/20201029082159/https://nycruns.com/race/nycruns-cocoa-classic-5k---10k" "NYCRUNS Cocoa Classic 5K" "sunday, december 6, 2020 7 am"

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

test_url http://web.archive.org/web/20190923170820/https://runsignup.com/Race/NY/Brooklyn/PPTCTurkeyTrot?remMeAttempt=  'PPTC Turkey Trot' 'thu november 28 2019'


test_url http://web.archive.org/web/20200219182317/https://www.nyrr.org/races/nyrrnewportfiesta5k 'NYRR Newport Fiesta 5K' 'may 2, 2020 5:00 pm' "location: 'li:parent-of(h2:contains(\"Location\")) div'" 'Jersey City'

test_url 'http://web.archive.org/web/20201023174217/https://ultrasignup.com/register.aspx?did=79440' 'Angry Tortoise 25K/50K' 'february 6, 2021 07:30:00' '' 'Bryceville, FL' 'http://web.archive.org/web/20201023174217/http://www.floridastriders.com/angrytortoise'

if [ ! "${SKIP_TESTS:-}" ]
then
    date +%s > "$test_success_timestamp_file"
fi

echo # after progress no-newline echos

if [ "$(basename "$0")" == "racetocal.sh" ]
then
  url="$1"

  #if [[ "$($CURL "$url" | grep  "403 Forbidden" )" != "" && "$CURL" == *cache_get* ]]
  #then
    #echo RETRYING DUE TO 403 2>&1
    ## try again
    #cache_get 0 "$url" > /dev/null
  #fi

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

  if [ "$arg_location" ]
  then
    location="$arg_location"
  else
    location="$(get_race_location "$url")"
  fi

  returned_url="$(get_race_url "$url")"
  if [ "$returned_url" != "$url" ]
  then
    url="$url  /  $returned_url"
  fi


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
  echo "location=\"$location\""
  set -o xtrace
  addrace.sh "$title" "$date" "$url" "" "$location"
fi
