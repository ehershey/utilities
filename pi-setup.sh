#!/bin/sh
#
# autoupdate_version = 28
#
# Set up new Raspberry Pi
#
#
# Usage: pi-setup.sh <hostname> [ <ip> ]
#
# Requires wifi password in wifi-password.txt in the same directory as the script
# Requires opensensors password in pi-opensensors-password.txt in the same directory as the script
#

set -o nounset
set -o errexit
set -o xtrace

#WIFINETWORK="seveneleven"
WIFINETWORK="Fios-IT5TV"
WIFIPASSWORD="$(cat $(dirname $0)/wifi-password.txt)"

OPENSENSORSUSERNAME=ehershey
OPENSENSORSDEVICEID=1378
OPENSENSORSPASSWORD="$(cat $(dirname $0)/pi-opensensors-password.txt)"
OPENSENSORSTOPIC="/users/ehershey/my/big/red/button"

PAYLOAD_AWS_SECRET_ACCESS_KEY="$(cat $(dirname $0)/payload-secret.txt)"
PAYLOAD_AWS_ACCESS_KEY_ID="$(cat $(dirname $0)/payload-key_id.txt)"


HOSTNAME=${1:-""}


if [ ! "$HOSTNAME" ]
then
  echo "Usage: $0 <pi hostname> [ <ip address> ]"
  exit 2
fi

if [ "${2:-}" ]
then
  connect_to=$2
else
  connect_to=$1
fi



ssh-copy-id pi@$connect_to

ssh="ssh -t pi@$connect_to"
teessh="ssh pi@$connect_to" # don't allocate a tty so input can come from script

if ! $ssh echo test > /dev/null
then
  echo "Can't ssh to pi@connect_to"
  exit 2
fi

$ssh sudo hostname $HOSTNAME

$ssh sudo apt-get --yes update
packages="mosquitto mosquitto-clients s3cmd wiringpi lsof libattr1-dev bc cron-apt influxdb-client chef jq python-smbus i2c-tools python3-pip"

# https://learn.adafruit.com/adafruit-mini-pitft-135x240-color-tft-add-on-for-raspberry-pi/python-setup
packages="$packages python3-pil ttf-dejavu python3-numpy"
$ssh sudo apt-get --yes install $packages
$ssh "systemctl is-enabled influxdb && sudo systemctl disable influxdb" || true
$ssh "systemctl status influxdb && sudo systemctl stop influxdb" || true

remove_packages="lightdm influxdb"
$ssh sudo apt-get --yes purge $remove_packages
$ssh sudo apt autoremove

if ! $ssh sudo grep -q "$WIFINETWORK" /etc/wpa_supplicant/wpa_supplicant.conf
then
  $teessh "sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null"  <<EOF
network={
  ssid="$WIFINETWORK"
  psk="$WIFIPASSWORD"
  key_mgmt=WPA-PSK
}
EOF
fi

if ! $ssh sudo grep -q "root:" /etc/aliases
then
  $teessh "sudo tee -a /etc/aliases > /dev/null"  <<EOF
root: pi-root-$HOSTNAME@ernie.org
EOF
  $ssh sudo newaliases
fi
if ! $ssh sudo grep -q "pi:" /etc/aliases
then
  $teessh "sudo tee -a /etc/aliases > /dev/null"  <<EOF
pi: pi-pi-$HOSTNAME@ernie.org
EOF
  $ssh sudo newaliases
fi




if ! $ssh ls /etc/udev/rules.d/50-big-red-button.rules >/dev/null
then
  $teessh "sudo tee /etc/udev/rules.d/50-big-red-button.rules > /dev/null" <<EOF
ACTION=="add", ATTRS{idVendor}=="1d34", ATTRS{idProduct}=="000d", SYMLINK+="big_red_button", MODE="0666", RUN+="/usr/bin/mosquitto_pub -h opensensors.io -t $OPENSENSORSTOPIC -m Add -i $OPENSENSORSDEVICEID -u $OPENSENSORSUSERNAME -P $OPENSENSORSPASSWORD"
ACTION=="remove", ATTRS{idVendor}=="1d34", ATTRS{idProduct}=="000d", RUN+="/usr/bin/mosquitto_pub -h opensensors.io -t $OPENSENSORSTOPIC -m Add -i $OPENSENSORSDEVICEID -u $OPENSENSORSUSERNAME -P $OPENSENSORSPASSWORD"
EOF
fi

python3_packages="setuptools RPI.GPIO adafruit-blinka"

# https://learn.adafruit.com/pi-hole-ad-blocker-with-pi-zero-w/install-pioled

python3_packages="$python3_packages adafruit-circuitpython-ssd1306 requests"

# https://learn.adafruit.com/adafruit-mini-pitft-135x240-color-tft-add-on-for-raspberry-pi/python-setup

python3_packages="$python3_packages adafruit-circuitpython-rgb-display spidev"

$ssh sudo pip3 install --upgrade $python3_packages


$ssh AWS_ACCESS_KEY_ID=$PAYLOAD_AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY=$PAYLOAD_AWS_SECRET_ACCESS_KEY s3cmd get --force s3://erniepayloads/common/files/usr/local/bin/install-payload /tmp/install-payload
$ssh chmod 755 /tmp/install-payload
$ssh sudo /tmp/install-payload
