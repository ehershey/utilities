#!/bin/bash
#
# Kill alarm processes started by alarm.sh
#

osxmute
while ps auwx | grep -v grep | grep afplay
do
  sudo killall afplay
  sleep 1
  sudo killall afplay
done
