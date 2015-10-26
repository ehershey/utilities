#!/bin/sh
#
#
# Set up new Raspberry Pi
#
#
# Usage: pi-setup.sh <hostname>
#
# Requires wifi password in wifi-password.txt in the same directory as the script
# Requires opensensors password in pi-opensensors-password.txt in the same directory as the script
#

set -o nounset

WIFINETWORK="seveneleven"
WIFIPASSWORD="$(cat $(dirname $0)/wifi-password.txt)"

OPENSENSORSUSERNAME=ehershey
OPENSENSORSDEVICEID=1378
OPENSENSORSPASSWORD="$(cat $(dirname $0)/pi-opensensors-password.txt)"
OPENSENSORSTOPIC="/users/ehershey/my/big/red/button"

HOSTNAME=${1:-""}

if [ ! "$HOSTNAME" ]
then
  echo "Usage: $0 <pi hostname or ip address>"
  exit 2
fi

ssh-copy-id pi@$HOSTNAME

ssh="ssh -t pi@$HOSTNAME"

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

$ssh crontab <<'EOF'
* * * * * curl "http://ernie.org/hostupdate?name=eahpi2&ips=$(/sbin/ifconfig -a | grep inet | grep -v inet6 | grep -v 127.0.0.1 | cut -f2 -d: | cut -f1 -d\ | tr \\n \|)" >> /tmp/hostupdate.log
EOF

