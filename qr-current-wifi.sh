#!/bin/bash
#
# qr-current-wifi.sh
# - No command line arguments.
# 1. Determine current wifi network SSID
# 2. Pull wifi password from system keychain
# 3. Formulate URL to join wifi network
# 4. Output URL encoded as ansi QR code
#
# autoupdate_version = 15
#
set -o pipefail
set -o errexit
set -o nounset

if ! command -v qrencode >/dev/null
then
  brew install qrencode
fi

network="$(system_profiler SPAirPortDataType | awk '/Current Network/ {getline;$1=$1;print $0 | "tr -d ':'";exit}')"

echo "Network appears to be: $network"
password="$(security find-generic-password -wa "$network")"
echo "Password appears to be: $password"

url="WIFI:S:$network;T:WPA;P:$password;;"
echo "url: ${url}"
qrencode "${url}" -t ansi
