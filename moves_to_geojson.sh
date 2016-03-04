#!/bin/bash
#
#
# Take gps log data exported from the Moves api, formatted like this:
#[
#  {
#    "caloriesIdle": 1727,
#    "segments": [
#      {
#        "activities": [
#          {
#            "trackPoints": [],
#            ...
#          }
#        ],
#        "place": {
#          "location": {
#            "lon": -73.9636240385,
#            "lat": 40.6819810438
#          },
#          "type": "home",
#          "name": "Home",
#          "id": 64479773
#        },
#        "endTime": "20140418T143810Z",
#        "startTime": "20140418T025840Z",
#        "type": "place"
#      },
#      {
#        "activities": [
#          {
#            "trackPoints": [
#              {
#                "time": "20140418T143810Z",
#                "lon": -73.9636240385,
#                "lat": 40.6819810438
#              },
#
#
# Import it into mongodb to look like (trackPoints only):
# {
#   _id: blah,
#   loc : { type : "Point" ,
#         coordinates : [ 73.9879226, 40.7573039 ]
#   },
#   last_update: Date(1151381451000),
#   entry_date: Date(1151381451000),
#   entry_source: "latitude",
#   accuracy: 5,
# }
#
# Example usage:
#
# curl --silent "https://api.moves-app.com/api/v1/user/storyline/daily?pastDays=1&trackPoints=true&access_token=$MOVES_ACCESS_TOKEN" | moves_to_geojson.sh "Moves API" |  mongoimport --db ernie_org --collection gps_log
#
# Requires "jq" command line tool

if [ "$1" ]
then
  entry_source_sed="sed 's/^}$/, entry_source: \"$1\"}/g'"
else
  entry_source_sed="cat"
fi

cat | \
  (jq '{ segments: [ { activities: [ { trackPoints: [] } ] } ] } + .[] | ( { activities: [] } + .segments[] ) | .activities[] | .trackPoints[] ' || cat > /tmp/errors.txt ) | \
 sed 's/"time": "\(....\)\(..\)\(..\)T\(..\)\(..\)\(..\)Z"/entry_date: { "$date": "\1-\2-\3T\4:\5:\6.000-0000" }/g' | \
 sed 's/"time": "\(....\)\(..\)\(..\)T\(..\)\(..\)\(..\)-\([0-9][0-9][0-9][0-9]\)"/entry_date: { "$date": "\1-\2-\3T\4:\5:\6.000-\7" }/g' | \
 sed 's/"lon" *: *\(-*..\)/loc: { type: "Point", coordinates: [ \1/g' | \
 sed 's/"lat" *: *\(-*[0-9.][0-9.]*\)/\1]}/g' | \
 sed 's/^{/#{/g' | \
 tr -d \\n | \
 tr \# \\n | \
 # tr -d \\n  | \
 #sed 's/coordinates: *\[ *\([0-9.-][0-9.-]*\), *\([0-9.-][0-9.-]*\)\]/coordinates: [\2, \1]/g'  | \
 #tr -d \\n | \
 #tr \# \\n  | \
 #sed 's/"timestampMs" : "\([0-9][0-9]*\)"/entry_date: new Date(\1), last_update: new Date(\1)/g'    | \
 #sed 's/, *}/}/g' | \
 eval $entry_source_sed
