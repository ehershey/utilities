#!/bin/sh
#
#
# Retrieve Nest Thermostat state from the Nest API and store in MongoDB
#
#
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
curl --silent --show-error --location https://developer-api.nest.com/devices/thermostats/$NEST_DEVICE_ID.json\?auth\=$NEST_ACCESS_TOKEN | mongoimport --db nest --collection thermostat_log
