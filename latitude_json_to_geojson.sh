#!/bin/sh
#
#
# Take gps log data exported via google takeout, formated like this:
#
# {
#  "somePointsHidden" : false,
#  "locations" : [ {
#    "timestampMs" : "1396727143852",
#    "latitudeE7" : 408179548,
#    "longitudeE7" : -739620148,
#    "accuracy" : 114,
#    "velocity" : -1,
#    "heading" : -1,
#    "altitude" : 1
#  }, {
#    "timestampMs" : "1396727083818",
#    "latitudeE7" : 408194818,
#    "longitudeE7" : -739603787,
#    "accuracy" : 5,
#    "velocity" : 6,
#    "heading" : 210,
#    "altitude" : 1
#  }
#
# Import it into mongodb to look like: 
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
# latitude_json_to_geojson.sh "Latitude import" < LocationHistory.json | mongoimport --db ernie_org --collection locations

if [ "$1" ] 
then
  entry_source_sed="sed 's/}$/, entry_source: \"$1\"/g'"
else
  entry_source_sed="cat"
fi

cat | \
 tail -n +3 | \
 grep -vx '}' | \
 sed 's/^  } \]/}/' | \
 sed 's/^  }, {/}# {/g' | \
 sed 's/"locations" : \[//' | \
 sed 's/"latitudeE7" *: *00*,/loc: { type: "Point", coordinates: [ 0,/' | \
 sed 's/"longitudeE7" *: *00*,/0]},/' | \
 sed 's/"longitudeE7" *: *00*$/0]}/' | \
 sed 's/"latitudeE7" *: *\(-*..\)/loc: { type: "Point", coordinates: [ \1./' | \
 sed 's/"longitudeE7" *: *\(-*..\)\([0-9.][0-9.]*\)/\1.\2]}/' | \
 tr -d \\n  | \
 sed 's/coordinates: *\[ *\([0-9.-][0-9.-]*\), *\([0-9.-][0-9.-]*\)\]/coordinates: [\2, \1]/g'  | \
  tr -d \\n | \
 tr \# \\n  | \
 sed 's/"timestampMs" : "\([0-9][0-9]*\)"/entry_date: new Date(\1), last_update: new Date(\1)/g'    | \
 sed 's/, *}/}/g' | \
 eval $entry_source_sed
