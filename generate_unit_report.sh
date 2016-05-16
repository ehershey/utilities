#!/bin/bash

set -o errexit

date >&2

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

tempfile=$(mktemp /tmp/average_unit_report.XXXXXX)

$SCRIPT > "$tempfile"

old_md5=$(grep -v diffignore "$REPORT" | $md5)
new_md5=$(grep -v diffignore "$tempfile" | $md5)

echo "old_md5: $old_md5"
echo "new_md5: $new_md5"

if [ -s "$tempfile" -a "$old_md5" != "$new_md5" ]
then
  echo "Generating new report" >&2
  cat "$tempfile" > "$REPORT"
else
  echo "Not generating new report" >&2
fi

rm "$tempfile"
