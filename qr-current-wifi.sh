#!/bin/bash
#
# qr-current-wifi.sh
# - No command line arguments.
# 1. Determine current wifi network SSID
# 2. Pull wifi password from system keychain
# 3. Formulate URL to join wifi network
# 4. Output URL encoded as ansi QR code
#
# autoupdate_version = 14
#
set -o pipefail
set -o errexit
set -o nounset

if ! command -v qrencode >/dev/null
then
  brew install qrencode
fi

INTERFACES="en0 en1"

for INTERFACE in $INTERFACES
do
  if networksetup -getairportnetwork "$INTERFACE" >/dev/null 2>&1
  then
        network=$(networksetup -getairportnetwork "$INTERFACE" | cut -f2- -d: | sed 's/^ *//')
        if [ "$network" ]
        then
          break
        fi
  fi
done
echo "Network appears to be: $network"
password="$(security find-generic-password -wa "$network")"
echo "Password appears to be: $password"

url="WIFI:S:$network;T:WPA;P:$password;;"
echo "url: ${url}"
qrencode "${url}" -t ansi
