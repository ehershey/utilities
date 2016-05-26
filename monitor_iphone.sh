#!/bin/bash
#
# Turn bluetooth on when my iphone is connected via usb
#
# Requires Blueutil (https://github.com/toy/blueutil)
#
set -o errexit

export "PATH=/usr/sbin:/usr/local/bin:$PATH"

# To populate $iphone_serial
#
. "$(dirname "$0")"/monitor_iphone_env.sh

echo "iphone_serial: $iphone_serial"

found=$(system_profiler SPUSBDataType -xml | xpath "//string[contains(text(),'$iphone_serial')][preceding-sibling::*[1][contains(text(),'serial_num')]]" 2>&1 | grep $iphone_serial)

echo "usb output: $found"

if [ "$found" ]
then
  echo "blueutil power 1"
  blueutil power 1
fi
