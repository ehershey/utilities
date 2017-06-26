#!/bin/sh
moves_age_seconds=$(`dirname "$0"`/get_change_ages.sh  | grep moves_seconds_since_change | cut -f2 -d: | cut -f1 -d. | tr -d " ")
if [ "$moves_age_seconds" -gt 3600 ]
then
  echo "Moves data out of date! ($moves_age_seconds seconds)" | tee /dev/tty | mail moves-outofdate@ernie.org
  touch /tmp/moves-outofdate
elif [ -e /tmp/moves-outofdate ]
then
  echo "Moves data back up to date!" | tee /dev/tty | mail moves-outofdate@ernie.org
  rm /tmp/moves-outofdate
fi
