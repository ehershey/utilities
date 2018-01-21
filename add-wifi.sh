#!/bin/bash
#
set -o pipefail
set -o errexit
set -o nounset

INTERFACES="en0 en1"
WIFIDOC=~/Dropbox//PlainText/wifi.txt

for INTERFACE in `echo $INTERFACES`
do
  if networksetup -getairportnetwork $INTERFACE
  then
        network=$(networksetup -getairportnetwork $INTERFACE | cut -f2- -d: | sed 's/^ *//')
  fi
done
echo "Adding to $WIFIDOC"
if grep -q "$network" "$WIFIDOC"
then
  echo "WARNING: Appears to be duplicate"
fi
echo "Network appears to be: $network"
password="$(security find-generic-password -wa $network)"
echo "Password appears to be: $password"
echo -n "Enter location name: "
read location
entry="$location - $network / $password"
echo "Press enter to add entry, ^C to quit:"
echo "$entry"
read null
echo >> $WIFIDOC
date >> $WIFIDOC
echo "$entry" >> $WIFIDOC
