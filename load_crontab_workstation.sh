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


if [ ! -e "$FILEHOME/crontab-workstation.txt" ]
then
  echo "Can't find crontab-workstation.txt in $FILEHOME"
  exit 2
fi

if ! which -s ts
then
  # for "ts" command
  #
  brew install moreutils
fi


tempfile1=$(mktemp)
tempfile2=$(mktemp)

#cat "$FILEHOME/crontab-workstation.txt" | $command


$command -l > $tempfile1
cat "$FILEHOME/crontab-workstation.txt" > $tempfile2
if [[ ! "$(diff $tempfile1 $tempfile2)" ]]
then
  echo "No updates. Aborting."
  exit 1
fi
diff $tempfile1 $tempfile2
rm $tempfile1 $tempfile2
echo -n "Diff ok? (y/n): "
read ans
if [[ "$ans" == "y" ]]
then
  echo "Loading crontab."
  cat "$FILEHOME/crontab-workstation.txt" | $command
else
  echo Aborting.
fi


