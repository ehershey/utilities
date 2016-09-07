#!/bin/bash
#
# Sound alarm in X minutes
#
# Usage:
# alarm.sh [ <minutes> ]
#
# Requires:
# * afplay executable - https://developer.apple.com/library/mac/documentation/Darwin/Reference/Manpages/man1/afplay.1.html#//apple_ref/doc/man/1/afplay
# * ~/Dropbox/Misc/ascending.mp3 audio file
#
AUDIOFILE=~/Dropbox/Misc/ascending.mp3

MINUTES_DEFAULT=20

minutes="$1"
if [ ! "$minutes" ]
then
  minutes=$MINUTES_DEFAULT
fi

if [ "$2" ]
then
  echo "usage: $0 [ <minutes> ]"
  echo "Defaults to $MINUTES_DEFAULT minutes."
  exit 1
fi

if [ ! -s "$AUDIOFILE" ]
then
  echo "File \"$AUDIOFILE\" doeesn't exit"
  exit 2
fi

seconds=$(expr $minutes \* 60)
echo "Will alarm in $minutes minutes ($seconds seconds)"

osxnotify "Alarm in $minutes minutes"
date
sleep $seconds; ( afplay "$AUDIOFILE" ; afplay "$AUDIOFILE" ) & killall PandoraJam ; osxstop & osxnotify 'Move!'
