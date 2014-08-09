#!/bin/bash
# load crontab from crontab.txt and crontab.env
#
#
CRON_USER=ernie
FILEHOME=/home/ernie/git/utilities

if [ "$CRON_USER" != "$USER" ] 
then
  command="sudo crontab -u $CRON_USER"
else
  command="crontab"
fi

if [ ! -e "$FILEHOME/crontab.env" -o ! -e "$FILEHOME/crontab.txt" ] 
then
  echo "Can't find crontab.env or crontab.txt in $FILEHOME"
  exit 2
fi
cat "$FILEHOME/crontab.env" "$FILEHOME/crontab.txt" | $command 
