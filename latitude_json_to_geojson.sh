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
# latitude_json_to_geojson.sh < LocationHistory.json | mongoimport --db ernie_org --collection locations

