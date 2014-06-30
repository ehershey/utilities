#!/bin/bash
#
#
# Increase volume of audio files
#
#

if [ ! "$1" ]
then
  echo "usage: $0: <file> [ <file> ... ]"
  exit 1
fi

adjusted_files=""
for file in "$@"
do
  adjusted_file="adjusted-$file"
  ffmpeg -i "$file" -af volume=12 "$adjusted_file"
  adjusted_files="$adjusted_files\n$adjusted_file"
done

# TODO fix '-e' interpreted characters in filenames
#
echo -e "Adjusted files: $adjusted_files"
