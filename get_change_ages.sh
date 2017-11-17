#!/bin/sh
nest_seconds_since_change=$(echo '(Number(new Date()) - Number((db.thermostat_log.find().sort({ _id: -1}).limit(1).toArray()[0]._id).getTimestamp())) / 1000' | mongo --quiet nest)
moves_seconds_since_change=$(echo '(Number(new Date()) - Number((db.activities.find().sort({ _id: -1}).limit(1).toArray()[0]._id).getTimestamp())) / 1000' | mongo --quiet moves)
gps_log_seconds_since_change=$(echo '(Number(new Date()) - Number((db.gps_log.find().sort({ _id: -1}).limit(1).toArray()[0]._id).getTimestamp())) / 1000' | mongo --quiet ernie_org)
echo gps_log_seconds_since_change: $gps_log_seconds_since_change
echo moves_seconds_since_change: $moves_seconds_since_change
echo nest_seconds_since_change: $nest_seconds_since_change
