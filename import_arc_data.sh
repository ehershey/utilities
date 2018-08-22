#!/bin/sh
#
#
# Look for Arc export files in an 'incoming' directories; import
# them and mark that they're done via a 'completed' directory.
#
# Files are moved to a 'processing' directory while being processed.
#

set -o errexit
set -o nounset

base_dir=~/Dropbox/Misc/arc_import
incoming_dir="$base_dir/incoming"
processing_dir="$base_dir/processing"
completed_dir="$base_dir/completed"

gpx_dir=~/"Dropbox/Misc/Arc Export"

if [ ! -d "$incoming_dir" ]
then
  echo "no incoming dir: $incoming_dir"
  exit 2
fi

if [ ! -d "$processing_dir" ]
then
  echo "no processing dir: $processing_dir"
  exit 2
fi

if [ ! -d "$completed_dir" ]
then
  echo "no completed dir: $completed_dir"
  exit 2
fi

conversion_script=~/git/utilities/arc_data_to_geojson.sh
gpx_geojson_script=~/git/utilities/erniegps/gpx_to_geojson.py
gpx_summary_script=~/git/utilities/erniegps/gpx_to_daily_summary.py

entry_source="Arc GPX"

db='ernie_org'
gps_collection='gps_log'
summary_collection='daily_summary'

gps_import_cmd="mongoimport --db $db --collection $gps_collection"
summary_import_cmd="mongoimport --db $db --collection $summary_collection"

# 1. json data, remove as we process it
#
if [ "$(find "$incoming_dir/" -type f)" ]
then
  for incoming_file in "$incoming_dir"/*
  do
    basename="$(basename "$incoming_file")"
    processing_file="$processing_dir/$basename"
    completed_file="$completed_dir/$basename"
    if mv "$incoming_file" "$processing_file"
    then
      if "$conversion_script" < "$processing_file" | $gps_import_cmd
      then
        mv "$processing_file" "$completed_file"
      else
        mv "$processing_file" "$incoming_file"
      fi
    fi

  done
fi

# 2. gpx data into ernie_org.gps_log
#
if [ "$(find "$gpx_dir/" -name \*.gpx -type f)" ]
then
  # do the same for gpx files but don't remove them
  #
  find "$gpx_dir" -name \*.gpx | while read incoming_file
  do
    basename="$(basename "$incoming_file")"
    processing_file="$processing_dir/$basename"
    completed_file="$completed_dir/$basename"
    if [ ! -e "$completed_file" -o "$incoming_file" -nt "$completed_file" ]
    then
      if cp -prn "$incoming_file" "$processing_file"
      then
        if "$gpx_geojson_script" --entry-source "$entry_source" < "$processing_file" | $gps_import_cmd
        then
          mv "$processing_file" "$completed_file"
        else
          rm "$processing_file"
        fi
      fi
    fi
  done
fi

# 3. gpx data into ernie_org.daily_summary
#
if [ "$(find "$gpx_dir/" -name \*.gpx -type f)" ]
then
  # do the same for gpx files again, don't remove them, store completed under new name
  #
  find "$gpx_dir" -name \*.gpx | while read incoming_file
  do
    basename="$(basename "$incoming_file")"
    basename="rawgpx-$basename"
    processing_file="$processing_dir/$basename"
    completed_file="$completed_dir/$basename"
    if [ ! -e "$completed_file" -o "$incoming_file" -nt "$completed_file" ]
    then
      if cp -prn "$incoming_file" "$processing_file"
      then
        if "$gpx_summary_script" --entry-source "$entry_source" < "$processing_file" | $summary_import_cmd
        then
          mv "$processing_file" "$completed_file"
        else
          rm "$processing_file"
        fi
      fi
    fi
  done
fi

