#!/bin/sh
#
# Send email when Moves DB data transitions from stale to fresh or from fresh to stale.
#
# Use file to track the previous state of data's staleness. If it exists, data is out of date and notification has been sent. 
#
lockfile=/tmp/moves-outofdate
recipient=moves-outofdate@ernie.org
moves_age_seconds=$(`dirname "$0"`/get_change_ages.sh  | grep moves_seconds_since_change | cut -f2 -d: | cut -f1 -d. | tr -d " ")
if [ "$moves_age_seconds" -gt 3600 ]
then
  if [ ! -e "$lockfile" ]
  then
    echo "Moves data out of date! ($moves_age_seconds seconds)" | tee /dev/tty | mail $recipient
    touch $lockfile
  fi
elif [ -e $lockfile ]
then
  echo "Moves data back up to date!" | tee /dev/tty | mail $recipient
  rm $lockfile
fi
