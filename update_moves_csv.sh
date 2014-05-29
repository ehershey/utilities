#!/bin/bash
# Update moves.csv with values from Moves Service
# 
# Requires $MOVES_ACCESS_TOKEN environment variable
# or crontab.env in same directory
#
if [ ! "$MOVES_ACCESS_TOKEN" ]
then
  . "$(dirname "$0")"/crontab.env
fi
if [ ! "$MOVES_ACCESS_TOKEN" ]
then
  echo "No \$MOVES_ACCESS_TOKEN defined."
  exit 2
fi
echo update_moves_csv.sh starting
date
curl "https://api.moves-app.com/api/v1/user/summary/daily?pastDays=10&access_token=$MOVES_ACCESS_TOKEN" | ~ernie/git/utilities/print_moves_csv.py > /tmp/moves-new.csv ; touch ~ernie/Dropbox/Web/moves.csv ; cat ~ernie/Dropbox/Web/moves.csv >> /tmp/moves-new.csv ; cat /tmp/moves-new.csv | sort --key 5,5 --field-separator=, --reverse --numeric | sort --key=1,1 --field-separator=, --reverse --unique > ~ernie/Dropbox/Web/moves.csv
export PATH=$PATH:/usr/sbin
chown :apache ~ernie/Dropbox/Web/moves.csv
chmod g+rwx ~ernie/Dropbox/Web/moves.csv
