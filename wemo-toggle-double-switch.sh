#!/bin/sh
#
# When a Flic button is pressed, toggle set of Wemo switches
#
# If both are on - turn them off
# If one or both are off - turn them on
# If one is on and one is off - turn on the one that's off
#

set -o nounset
set -o errexit

DEVICE1="Lab Light Switch"
DEVICE2="Ernie Desk Lamp"

PATH="$PATH:/usr/local/bin"

# Returns "0" for off and "1" for on
#
DEVICE1_STATUS=$(wemo switch "$DEVICE1" status)
DEVICE2_STATUS=$(wemo switch "$DEVICE2" status)

if [[ "$DEVICE1_STATUS" = "1" && "$DEVICE2_STATUS" = "1" ]]
then
  wemo switch "$DEVICE1" off
  wemo switch "$DEVICE2" off
else
  if [[ "$DEVICE1_STATUS" = "0" ]]
  then
    wemo switch "$DEVICE1" on
  fi
  if [[ "$DEVICE2_STATUS" = "0" ]]
  then
    wemo switch "$DEVICE2" on
  fi
fi
