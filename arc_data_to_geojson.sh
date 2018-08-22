#!/bin/sh
#
#
# Take arc data downloaded from export site and translate it into geojson:
#
# {
#   "entry_date" : ISODate("2018-07-20T18:51:04Z"),
#   "loc" :
#   {
#       "type" : "Point",
#       "coordinates" : [ -73.98762, 40.757194 ]
#   },
#   "entry_source" : "Moves API" 
# }
#
# Arc data looks like:
# [
#   {
#     "967C0432-5B4E-4307-A69F-18580FFFE234": {
#       "recordName": "967C0432-5B4E-4307-A69F-18580FFFE234",
#       "recordType": "HistoryItem",
#       "fields": {
#       ...
#         "location": {
#           "value": {
#             "latitude": 40.68526224086859,
#             "longitude": -73.97182662706706,
#             "horizontalAccuracy": 0,
#             "altitude": 0,
#             "verticalAccuracy": -1,
#             "speed": -1,
#             "course": -1,
#             "timestamp": 1532281260623
#           },
#           "type": "LOCATION"
#         },
#       },
#       "activityRecords": [
#         [
#           "783A4F5D-3438-46F6-9F1E-AF66632334B9",
#           {
#             "recordName": "783A4F5D-3438-46F6-9F1E-AF66632334B9",
#             "recordType": "ActivityEvent",
#             "fields": {
#             ...
#               "location": {
#                  "value": {
#                    "latitude": 40.68526224086859,
#                   "longitude": -73.97182662706706,
#                    "horizontalAccuracy": 0,
#                    "altitude": 0,
#               ...
#       ...
#   },
#   ... repeat
# ]

set -o errexit
set -o nounset
cat | jq '..|.location? | select(.value) | .value | { entry_date: { "$date": (.timestamp /1000 | gmtime | todate)} , loc: { type: "Point", coordinates: [ .longitude, .latitude ] }, entry_source: "Arc App"} '
