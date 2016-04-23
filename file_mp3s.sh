#!/bin/bash
#
# usage: file_mp3s.sh <source> <target>
#
# for example:
#
# file_mp3s.sh [ --dryrun ] [ --nocache ] "/cygdrive/x/LCD Soundsystem" /cygdrive/x
#
# Depends on:
# generate_normalized_mp3_path.sh in path

nocache=""
dryrun=""

while [ "$3" ]
do
  if [ "$1" = "--nocache" ]
  then
    nocache=1
    shift
  elif [ "$1" = "--dryrun" ]
  then
    dryrun=1
    shift
  else
    echo "Invalid argument: $1"
    exit 2
  fi
done

source="$1"
target="$2"

if [ ! "$source" -o ! "$target" ]
then
  echo "usage: $0 <source> <target>"
  exit 2
fi

tempfile=/tmp/file_mp3s_list.$$..txt
DEFAULT_CACHE_TIMEOUT=300

if [ "$nocache" ]
then
  cache_timeout=0
else
  cache_timeout=$DEFAULT_CACHE_TIMEOUT
fi

cache_run $cache_timeout "find \"$source\" -type f" > $tempfile


total_files=`wc -l < $tempfile`
echo "total_files: $total_files"

i=0
while read file
do
  echo "examining $file"
  i=`expr $i + 1`
  echo "($i of $total_files)"
  newfile="`cache_run 86400 \"generate_normalized_mp3_path.sh  \\\"$file\\\"\"`"
  if [ ! "$newfile" ]
  then
    echo "no path generated"
    continue
  fi
  newfile="$target/$newfile"
  lcfile="`echo \"$file\" | tr A-Z a-z | sed 's#//#/#g'`"
  lcnewfile="`echo \"$newfile\" | tr A-Z a-z | sed 's#//#/#g'`"
  echo "file: >$file<"
  echo "newfile: >$newfile<"
  if [ "$lcfile" = "$lcnewfile" ]
  then
    echo "file is already in generated path"
    continue
  else
    ls -l "$file" "$newfile"  2>/dev/null
    newdir="`dirname \"$newfile\"`"
    if [ ! -e "$newdir" ]
    then
      mkdir -p "$newdir"
    fi
    if [ ! -e "$newfile" ]
    then
      echo moving file
      echo mv "$file" "$newfile"
      if [ ! "$dryrun" ]
      then
        mv "$file" "$newfile"
      fi
    else
      oldsize="`ls -l \"$file\" | awk '{print $5}'`"
      newsize="`ls -l \"$newfile\" | awk '{print $5}'`"
      if [ "$oldsize" = "$newsize" -a -e "$file" -a "`wc -c < \"$file\"`" -ne 0 ]
      then
        echo "files are same size, deleting old version"
        echo rm "$file"
        if [ ! "$dryrun" ]
        then
          rm "$file"
        fi
      else
        # echo "sizes of old ($oldsize) and new ($newsize) differ, not sure what to do!"
        if [ "$oldsize" -lt "$newsize" -a -e "$newfile" -a "`wc -c < \"$newfile\"`" -ne 0 ] # We know newfile exists from check above, but check again for clarity
        then
          echo "deleting smaller file ($file)"
          echo rm "$file"
          if [ ! "$dryrun" ]
          then
            rm "$file"
          fi
        fi
        if [ "$newsize" -lt "$oldsize"  -a -e "$file" -a "`wc -c < \"$file\"`" -ne 0 ]
        then
          echo "deleting smaller file ($newfile)"
          echo rm "$newfile"
          if [ ! "$dryrun" ]
          then
              rm "$newfile"
          fi
          echo mv "$file" "$newfile"
          if [ ! "$dryrun" ]
          then
            mv "$file" "$newfile"
          fi
        fi
      fi
    fi
  fi
done < $tempfile

perl -MFile::Find -e"finddepth(sub{rmdir},shift)" "$source"

