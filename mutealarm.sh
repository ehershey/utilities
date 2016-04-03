#!/bin/bash
#
# Kill alarm processes started by alarm.sh
#
# Works best with sudoers addition:
#
# %admin ALL=NOPASSWD:/usr/bin/killall afplay # for alarmkill.sh

osxmute
while ps auwx | grep -v grep | grep afplay
do
  sudo killall afplay
  sleep 1
  sudo killall afplay
done
