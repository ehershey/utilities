#!/bin/sh
#
# Post battery state and current wifi network to influxdb in MacOS
#
# Will error if no battery present
#
set -o nounset
set -o errexit

DB=ernie_org
MEASUREMENT=battery
WIFI_INTERFACE=en0

if pmset -g ps  | grep -q "AC Power"
then
  battery_state="charging" # charging, unplugged, or full
else
  battery_state="unplugged"
fi

device_id="$(hostname -s)"

wifi="$(networksetup -getairportnetwork en0 | cut -f2 -d: | sed 's/^ *//' | sed 's/ /\\ /g')"
battery_level="$(pmset -g ps | grep InternalBattery | cut -f1 -d\; | cut -f2 -d\) | tr -d \\t% | sed 's/^ */0./' ) "

# insert battery,battery_state=unplugged,device_id=eahmb12,wifi=EAH3\ Guest\ Wifi battery_level=0.50

set -o verbose
influx -database "${DB}" -execute "insert ${MEASUREMENT},battery_state=${battery_state},device_id=${device_id},wifi=${wifi} battery_level=${battery_level}"
