#!/bin/bash
#
# Kill alarm processes started by alarm.sh
#

osxmute
while ps auwx | grep -v grep | grep afplay
do
  killall afplay
  sleep 1
  killall afplay
done
