#!/bin/bash
# load crontab from crontab-workstation.txt
#
#
CRON_USER=ernie
FILEHOME=/Users/ernie/git/utilities
HOSTNAME_PATTERN1="imac"
HOSTNAME_PATTERN2="mba"
HOSTNAME_PATTERN3="mbp"

if [ "$CRON_USER" != "$USER" ]
then
  command="sudo crontab -u $CRON_USER"
else
  command="crontab"
fi

if [ ! "`hostname -s | grep $HOSTNAME_PATTERN1`" -a ! "`hostname -s | grep $HOSTNAME_PATTERN2`" -a ! "`hostname -s | grep $HOSTNAME_PATTERN3`" ]
then
  echo "Incorrect hostname: (looks like: $HOSTNAME, should contain: \"$HOSTNAME_PATTERN1\" or \"$HOSTNAME_PATTERN2\" or \"$HOSTNAME_PATTERN3\")"
  exit 3
fi

# for "ts" command
#
brew install moreutils

if [ ! -e "$FILEHOME/crontab-workstation.txt" ]
then
  echo "Can't find crontab-workstation.txt in $FILEHOME"
  exit 2
fi
cat "$FILEHOME/crontab-workstation.txt" | $command