#!/bin/sh
#
# Notify changes in bluetooth connected devices
#


# TODO support multiple exclude devices
#
EXCLUDE="eahmbp\|eahxs\|Ernie.s.MacBook"

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

TEST=""
#TEST=1

if [ "$TEST" ]
then
  echo 'ODT Privates BLUE' > $now_list
fi

diff "$last_list" "$now_list" >> "$log"

diff "$last_list" "$now_list" > "$tempfile"

if [ "$EXCLUDE" ]
then
  exclude_command="grep -vE $EXCLUDE"
else
  exclude_command="cat"
fi


grep ^\< "$tempfile" | sed 's/^< //' | LANG=en_us eval $exclude_command | while read device
do
  terminal-notifier -title DISCONNECTED -message "$device"
  echo "DISCONNECTED - $device" >> "$log"
  echo "set:" >> "$log"
  set >> "$log"
done

grep ^\> "$tempfile" | sed 's/^> //' | LANG=en_us eval $exclude_command | while read device
do
  terminal-notifier -title CONNECTED -message "$device"
  echo "CONNECTED - $device" >> "$log"
  echo "env:" >> "$log"
  env >> "$log"
done

if [ ! "$TEST" ]
then
  cp "$now_list" "$last_list"
fi
