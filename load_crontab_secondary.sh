#!/bin/bash
# load crontab from crontab-secondary.txt and crontab.env
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

if [ ! -e "$FILEHOME/crontab.env" -o ! -e "$FILEHOME/crontab-secondary.txt" ] 
then
  echo "Can't find crontab.env or crontab-secondary.txt in $FILEHOME"
  exit 2
fi
cat "$FILEHOME/crontab.env" "$FILEHOME/crontab-secondary.txt" | $command 
