#!/bin/bash

INTERFACE=en0
WIFIDOC=~/Dropbox//PlainText/wifi.txt
network=$(networksetup -getairportnetwork $INTERFACE | cut -f2- -d: | sed 's/^ *//')
echo "Network appears to be: $network"
echo -n "Enter password: "
read password
echo -n "Enter location name: "
read location
entry="$location - $network / $password"
echo "Press enter to add entry:"
echo "$entry"
read null
echo >> $WIFIDOC
date >> $WIFIDOC
echo "$entry" >> $WIFIDOC