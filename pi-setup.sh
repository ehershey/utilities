#!/bin/sh
#
#
# Set up new Raspberry pi
#
#
# Usage: pi-setup.sh <hostname>
#
# Put wifi password in wifi-password.txt in the same directory as the script
# Put opensensors password in pi-opensensors-password.txt in the same directory as the script
#

set -o nounset

WIFINETWORK="seveneleven"
WIFIPASSWORD="$(cat $(dirname $0)/wifi-password.txt)"

OPENSENSORSUSERNAME=ehershey
OPENSENSORSDEVICEID=1378
OPENSENSORSPASSWORD="$(cat $(dirname $0)/pi-opensensors-password.txt)"
OPENSENSORSTOPIC="/users/ehershey/my/big/red/button"

HOSTNAME="$1"

ssh-copy-id pi@$HOSTNAME

ssh="ssh pi@$HOSTNAME"

if ! $ssh echo test > /dev/null
then
  echo "Can't ssh to pi@HOSTNAME"
  exit 2
fi

$ssh sudo apt-get install mosquitto mosquitto-clients

if ! $ssh sudo grep -q "$WIFINETWORK" /etc/wpa_supplicant/wpa_supplicant.conf
then
  cat | $ssh "sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null"  <<EOF
network={
  ssid="$WIFINETWORK"
  psk="$WIFIPASSWORD"
  key_mgmt=WPA-PSK
}
EOF
fi

if ! $ssh ls /etc/udev/rules.d/50-big-red-button.rules >/dev/null
then
  cat | $ssh "sudo tee /etc/udev/rules.d/50-big-red-button.rules > /dev/null" <<EOF
ACTION=="add", ATTRS{idVendor}=="1d34", ATTRS{idProduct}=="000d", SYMLINK+="big_red_button", MODE="0666", RUN+="/usr/bin/mosquitto_pub -h opensensors.io -t $OPENSENSORSTOPIC -m Add -i $OPENSENSORSDEVICEID -u $OPENSENSORSUSERNAME -P $OPENSENSORSPASSWORD"
ACTION=="remove", ATTRS{idVendor}=="1d34", ATTRS{idProduct}=="000d", RUN+="/usr/bin/mosquitto_pub -h opensensors.io -t $OPENSENSORSTOPIC -m Add -i $OPENSENSORSDEVICEID -u $OPENSENSORSUSERNAME -P $OPENSENSORSPASSWORD"
EOF
fi

