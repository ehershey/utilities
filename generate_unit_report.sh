#!/bin/bash

set -o errexit

date

SCRIPT=~ernie/git/utilities/unit_report.py
REPORT=~ernie/Dropbox/Web/goeverywhere/unit_report.html


if which md5 &>/dev/null
then
  md5=md5
elif which md5sum &> /dev/null
then
  md5=md5sum
else
  # don't use checksum for cache file
  #
  md5=cat
fi

runtimestamp=$(date +%Y%m%d%H%M%S)

tempfile=$(mktemp /tmp/average_unit_report.XXXXXX)
trap "rm $tempfile" exit

$SCRIPT --run-timestamp "$runtimestamp" > "$tempfile"

old_md5=$(grep -v diffignore "$REPORT" | $md5)
new_md5=$(grep -v diffignore "$tempfile" | $md5)

echo "old_md5: $old_md5"
echo "new_md5: $new_md5"

if [ -s "$tempfile" -a "$old_md5" != "$new_md5" ]
then
  echo "Generating new report"
  echo "DIFF:"
  diff "$REPORT" "$tempfile" || true
  ls -l "$tempfile"
  echo "old_md5: $old_md5"
  echo "new_med5: $new_md5"
  cp -pri "$REPORT" "$REPORT.$runtimestamp"
  cat "$tempfile" > "$REPORT"
  date="$(date +%Y-%m-%d)"
  (echo "Updated https://goeverywhere.ernie.org/unit_report.html" ; echo ; echo ; diff "$REPORT.$runtimestamp" "$REPORT" ) | mail -s "Unit Report Update $date" unit-notifier@ernie.org
else
  echo "Not generating new report"
fi
find `dirname $REPORT` -path $REPORT.\* -mtime +7 -exec rm {} \;
