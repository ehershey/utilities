#!/bin/bash
# 
# Sound alarm in X minutes
# 
# Usage: 
# alarm.sh <minutes>
#
# Requires:
# "at" service - https://developer.apple.com/library/mac/documentation/Darwin/Reference/Manpages/man1/at.1.html#//apple_ref/doc/man/1/at
# afplay executable - https://developer.apple.com/library/mac/documentation/Darwin/Reference/Manpages/man1/afplay.1.html#//apple_ref/doc/man/1/afplay
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
