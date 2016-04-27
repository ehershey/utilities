#!/bin/bash
#
# Take a file, generate a standard path for it using the id3v2 utility
#
set -o pipefail
set -o errexit
set -o nounset


# --noconvert disables attempting to convert idv2 to idv3
#
if [ "${1:-}" = "--noconvert" ]
then
  noconvert=1
  shift
else
  noconvert=""
fi


file="${1:-}"


if [ ! "$file" ]
then
  echo "usage: $0 <filename>"
  exit 3
fi

extension=`echo "$file" | sed 's/.*\.//'`

if which id3info >/dev/null 2>&1
then
  artist=`id3info "$file" | grep  "Band/orchestra/accompaniment" | cut -f2 -d: | sed 's/^[ 	]*\(.*\)[ 	]*$/\1/g'`

  if [ ! "$artist" ]
  then
    artist=`id3info "$file" | grep  "=== TPE2" | cut -f2 -d: | sed 's/^[ 	]*\(.*\)[ 	]*$/\1/g'`
  fi
  if [ ! "$artist" ]
  then
    artist=`id3info "$file" | grep  "=== TP1" | cut -f2 -d: | sed 's/^[ 	]*\(.*\)[ 	]*$/\1/g'`
  fi
  if [ ! "$artist" ]
  then
    artist=`id3info "$file" | grep  "=== TPE1" | cut -f2 -d: | sed 's/^[ 	]*\(.*\)[ 	]*$/\1/g'`
  fi
  title=`id3info "$file" | grep  "Title/songname/content description" | cut -f2 -d: | sed 's/^[ 	]*\(.*\)[ 	]*$/\1/g'`
  album=`id3info "$file" | grep  "Album/Movie/Show title" | cut -f2 -d: | sed 's/^[ 	]*\(.*\)[ 	]*$/\1/g'`
  track=`id3info "$file" | grep  "Track number/Position in set" | cut -f2 -d: | sed 's/^[ 	]*\(.*\)[ 	]*$/\1/g' | cut -f1 -d/ | sed 's/^0*//'`
else

  if [ "`id3v2  -R "$file" 2>/dev/null | grep 'No ID3 tag'`" ]
  then
    title=`id3 -l -R "$file" 2>/dev/null | grep ^Title: | cut -f2- -d\  | sed 's/[ 	]*$//'`
    artist=`id3 -l -R "$file" 2>/dev/null | grep ^Artist: | cut -f2- -d\  | sed 's/[ 	]*$//'`
    album=`id3 -l -R "$file" 2>/dev/null | grep ^Album: | cut -f2- -d\  | sed 's/[ 	]*$//'`
    track=`id3 -l -R "$file" 2>/dev/null | grep ^Track: | cut -f2- -d\  | sed 's/[ 	]*$//' | sed 's/^0*//'`
  else


    artist=`id3v2 -R "$file" 2>/dev/null | egrep TP2\|TPE2 | cut -f2- -d\  | sed 's/[ 	]*$//'`
    if [ ! "$artist" ]
    then
      artist=`id3v2 -R "$file" 2>/dev/null | egrep TP1\|TPE1 | cut -f2- -d\  | sed 's/[ 	]*$//'`
    fi

    album=`id3v2 -R "$file" 2>/dev/null | grep TAL | cut -f2- -d\  | sed 's/[ 	]*$//'`
    title=`id3v2 -R "$file" 2>/dev/null | egrep ^TT2:\|^TIT2: | cut -f2- -d\  | sed 's/[ 	]*$//'`
    track=`id3v2 -R "$file" 2>/dev/null | egrep ^TRK:\|^TRCK: | cut -f2- -d\  | cut -f1 -d/ | sed 's/[ 	]*$//' | sed 's/^0*//'`
  fi

  if [ ! "$artist" -a ! "$album" -a ! "$title" -a ! "$track" ]
  then
    artist=`id3v2 -l "$file" | egrep TP2\|TPE2 | sed 's/.*: //'`
    if [ ! "$artist" ]
    then
      artist=`id3v2 -l "$file" | egrep TP1\|TPE1 | sed 's/.*: //'`
    fi
    album=`id3v2 -l "$file"| grep TAL | cut -f2- -d: | sed 's/^ //'`
    title=`id3v2 -l "$file"  | egrep ^TT2\|^TIT2 | sed 's/.*: //'`
    track=`id3v2 -l "$file" | egrep ^TRK\|^TRCK | sed 's/.*: //' | sed 's/\/.*//' | sed 's/^0*//'`
  fi
fi

  #echo "artist: $artist" >&2
  #echo "album: $album" >&2
  #echo "title: $title" >&2
  #echo "track: $track" >&2

dirname="$artist/$album"
if [ "$track" ]
then
  filename=`printf "%02d " $track`
fi
filename="$filename$title.$extension"

if [ "$title" -a "$artist" -a "$album" ]
then
  echo "$dirname/$filename"
else
  echo "Can't determine file info ($artist/$album/$title)" >&2
  if [ "$(which id3v2 2>/dev/null)" -a "$extension" = "mp3" -a ! "$noconvert" ]
  then
    id3v2 -C "$file" >&2
    $0 --noconvert "$file"
    exit $?
  else
    exit 4
  fi
fi



