#!/bin/bash
#
#
# Move images saved with generic names from Marathon Foto to meaningful names
#
#
# For example:
#
# Z.jpeg
# Z (1).jpeg
# Z (2).jpeg


set -o errexit
set -o nounset

TITLE_PREFIX="${1:-}"

if [ ! "$TITLE_PREFIX" ]
then
  echo "Usage: $0 <title prefix>"
  exit 2
fi

# sorting nastiness to do numeric sort on part of alphanumeric field
# From http://unix.stackexchange.com/questions/41655/how-to-sort-the-string-which-combined-with-string-numeric-using-bash-script/41656#41656

if ! ls -1 Z* >/dev/null 2>&1
then
  echo "No Z files to rename"
  exit 3
fi
ls -1 Z* | sed 's/\([0-9]\)/;\1/' | sort -n -t\; -k2,2 | tr -d ';' | while read file
do
  echo "file: $file"
  i=0
  while true
  do
    let i=i+1
    new_file="$TITLE_PREFIX $i.jpeg"
    if [ ! -e "$new_file" ]
    then
      break
    fi
  done
  echo mv "$file" "$new_file"
  mv "$file" "$new_file"
done
