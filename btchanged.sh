#!/bin/sh
#
# Notify changes in bluetooth connected devices
#


# TODO support multiple exclude devices
#
EXCLUDE="eahmbp"

if [ -e ~/.bashrc ]
then
  . ~/.bashrc
fi

if ! which -s terminal-notifier
then
  echo "Missing terminal-notifier executable in path" >&2
  echo "To fix, run:" >&2
  echo "  brew install terminal-notifier" >&2
  exit 2
fi

last_list=/tmp/btold
now_list=/tmp/btnow

log=/tmp/btlog

lsbt=~ernie/git/utilities/lsbt

tempfile="$(mktemp)"

date >> "$log"

if [ ! -e "$last_list" ]
then
  $lsbt -c > "$last_list"
fi

$lsbt -c > "$now_list"
diff "$last_list" "$now_list" >> "$log"

diff "$last_list" "$now_list" > "$tempfile"

if [ "$EXCLUDE" ]
then
  exclude_command="grep -v \"$EXCLUDE\" "
else
  exclude_command="cat"
fi



grep ^\< "$tempfile" | sed 's/^< //' | $exclude_command | while read device
do
  terminal-notifier -title DISCONNECTED -message "$device"
done

grep ^\> "$tempfile" | sed 's/^> //' | $exclude_command | while read device
do
  terminal-notifier -title CONNECTED -message "$device"
done

cp "$now_list" "$last_list"
