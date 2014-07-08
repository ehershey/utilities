#!/bin/bash
# 
# Sound alarm in X minutes
# 
# Usage: 
# alarm.sh <minutes>
#
# Requires:
# at service
# afplay executable
# ~/Dropbox/Misc/ascending.mp3 audio file
#
AUDIOFILE=~/Dropbox/Misc/ascending.mp3

minutes="$1"
if [ ! "$minutes" ] 
then
  echo "usage: $0 <minutes>"
  exit 1
fi
echo "(afplay "$AUDIOFILE" ; afplay "$AUDIOFILE" ) & killall PandoraJam iTunes iTunesHelper mdworker" | at now + $minutes minutes
