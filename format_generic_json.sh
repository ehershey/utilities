#!/usr/bin/env bash
#
# Convert json into csv
#
# Optionally strip root objects containing arrays of target objects (e.g. ignore Reservation info in "aws ec2 describe-instances" output)
#
# Converts "Tags" arrays in objects into inline fields
#
# Arguments are fields to include (and header), and number of top level objects to ignore
#
set -o nounset
set -o pipefail
set -o errexit

if [ ! "${1:-}" ]
then
  echo "usage: format_generic_json.sh <comma separated header fields> [ <# of root objects to strip off> ]"
  exit 2
fi

fields="$1"

if [ "${2:-}" ]
then
  object_levels_to_prune="$2"
else
  object_levels_to_prune=""
fi

basename="$(basename "$0")"

tempfile=$(mktemp /tmp/$basename.XXXXXX)
tempfile2=$(mktemp /tmp/$basename.XXXXXX)

if [ "$object_levels_to_prune" ]
then
  for i in $(seq 1 $object_levels_to_prune)
  do
    cat | jq '.[][][] | select(type=="array") | .[]' > "$tempfile"
  done
else
    cat | jq '.[][]' > "$tempfile"
fi

# For each field, put a reference in a big string to pass to jq
#
field_references=""
for field in $(echo $fields | tr , \\n)
do
  if [ "$field_references" ]
  then
    field_references="${field_references} + \",\" + "
  fi
  field_references="${field_references}(.$field | tostring)"
done

# Move fields from Tags member array into objects
#
cat "$tempfile" | jq 'if has("Tags") then ( .Tags? | from_entries) else { }  end + ( . | del(.Tags?) )' > "$tempfile2"

# Display specified fields
#
cat "$tempfile2" | jq -r '('"$field_references"')'
