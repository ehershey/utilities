#!/bin/bash
#
CACHE_TIME=300
DIR=~/Dropbox/Misc/bash_history
tempfile=$(mktemp /tmp/global_history.XXXXXX)
tempfile2=$(mktemp /tmp/global_history.XXXXXX)


cache_run 300 "ls -tr \"$DIR\"/*" | xargs cat > "$tempfile"
while [ "$1" ]
do
  cat "$tempfile" | grep -i "$1" > "$tempfile2"
  cat "$tempfile2" > "$tempfile"
  shift
done

cat $tempfile
rm "$tempfile" "$tempfile2"
