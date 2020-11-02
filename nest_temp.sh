#!/bin/sh
#
#
# Set or Get Nest Thermostat target temperature
#
#

set -o errexit
set -o nounset
auth_file="$(dirname "$0")"/nest_auth

# Should contain
# NEST_ACCESS_TOKEN=xxx
# NEST_DEVICE_ID=xxx

if [ -e "$auth_file" ]
then
  . "$auth_file"
else
  echo "Can't find auth file: $auth_file"
  exit 1
fi

if [ "${1:-}" == "-h" ]
then
  echo "Usage: $0 [ <target farenheit temperature> ]"
  exit 2
fi


tempfile=`mktemp`
trap "echo ; echo tempfile: $tempfile; echo" INT

curl --silent --show-error --location https://developer-api.nest.com/devices/thermostats/$NEST_DEVICE_ID.json\?auth\=$NEST_ACCESS_TOKEN  > "$tempfile"
ambient_temp=$(jq .ambient_temperature_f < $tempfile)
old_target=$(jq .target_temperature_f < $tempfile)
echo "Ambient temperature: $ambient_temp"
echo "Old target: $old_target"
if [ "${1:-}" ]
then
  curl -X PUT -d '{"target_temperature_f": '"$1"'}' --silent --show-error --location https://developer-api.nest.com/devices/thermostats/$NEST_DEVICE_ID.json\?auth\=$NEST_ACCESS_TOKEN  > "$tempfile"
  new_target=$(jq .target_temperature_f < $tempfile)
  echo "New target: $new_target"
fi
rm "$tempfile"
