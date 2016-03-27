#!/bin/bash
#
# Filter audio files, increasing their volume
#
# Requires: ffmpeg
#
set -o errexit
set -o nounset
set -o pipefail

if [ ! "${1:-}" ]
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
echo -e "Adjusted files:\n$adjusted_files"
