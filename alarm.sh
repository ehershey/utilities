#!/bin/bash
#
# Sound alarm in X minutes
#
# Usage:
# alarm.sh [ <minutes> ]
#
# Requires:
# * "at" service - https://developer.apple.com/library/mac/documentation/Darwin/Reference/Manpages/man1/at.1.html#//apple_ref/doc/man/1/at
# ** Enable with:            launchctl load -w /System/Library/LaunchDaemons/com.apple.atrun.plist
# * afplay executable - https://developer.apple.com/library/mac/documentation/Darwin/Reference/Manpages/man1/afplay.1.html#//apple_ref/doc/man/1/afplay
# * ~/Dropbox/Misc/ascending.mp3 audio file
#
# Works best with sudo password exemptions:
#
# %admin ALL=NOPASSWD:/usr/bin/atq
# %admin ALL=NOPASSWD:/usr/bin/atrm
# %admin ALL=NOPASSWD:/usr/bin/at
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

echo "Will alarm in $minutes minutes" 
#echo "(afplay "$AUDIOFILE" ; afplay "$AUDIOFILE" ) & killall PandoraJam iTunes iTunesHelper mdworker" | at now + $minutes minutes
echo "(afplay "$AUDIOFILE" ; afplay "$AUDIOFILE" ) & killall PandoraJam ; osxstop & osxnotify 'Move!'" | sudo at now + $minutes minutes
osxnotify $(sudo atq | cut -f2-)
