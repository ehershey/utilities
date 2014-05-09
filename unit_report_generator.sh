#!/bin/sh

date >&2

SCRIPT=~/git/utilities/unit_report.py
REPORT=~/Dropbox/Web/goeverywhere/unit_report.html


tempfile=$(mktemp /tmp/average_unit_report.XXXXXX)

$SCRIPT > "$tempfile"

old_md5=$(grep -v diffignore "$REPORT" | md5sum)
new_md5=$(grep -v diffignore "$tempfile" | md5sum)

echo "old_md5: $old_md5"
echo "new_md5: $new_md5"

if [ "$old_md5" != "$new_md5" ]
then
  echo "Generating new report" >&2
  cat "$tempfile" > "$REPORT"
else
  echo "Not generating new report" >&2
fi

rm "$tempfile"
