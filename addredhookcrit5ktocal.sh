#!/bin/sh
CALENDAR="Rides and Races"
TODAY=$(date +%D)
REMINDER_MINUTES=$(echo '60 * 24 * 7' | bc -l)

output=$(gcalcli add --cal "$CALENDAR" --title "Red Hook Crit 5k 2015" --when '4/25/15 17:30' --duration 360 --description "http://redhookcrit5k.com/event-info/

url="$(echo "$output" | tr \ \\t \\n | grep http | head -1)"
open $url