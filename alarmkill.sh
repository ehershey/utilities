#!/bin/bash
#
# Kill alarm sounded by alarm.sh
#
# Usage:
# alarmkill.sh
#
# Works best with sudo password exemptions set via 'sudo visudo':
#
# %admin ALL=NOPASSWD:/usr/bin/killall afplay # for alarmkill.sh


( sudo killall afplay
sleep 2
sudo killall afplay) &
