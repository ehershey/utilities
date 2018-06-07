#!/bin/bash
#
# Connect bluetooth audio device in osx
#
# Use applescript to navigate bluetooth menu bar and select "Connect"
# in the submenu named $DEVICE_NAME.
#
# $DEVICE_NAME can be set in these ways, in descending precedence:
# 1) The command line
# 2) $BLUETOOTH_AUDIO_DEVICE_NAME environment variable set outside this script
# 3) $DEFAULT_DEVICE_NAME, set below
#
DEFAULT_DEVICE_NAME="ODT Privates"
DEVICE_NAME=${BLUETOOTH_AUDIO_DEVICE_NAME:-$DEFAULT_DEVICE_NAME}

# how long to wait for action to be visible after we believe it to have
# happened
#
TIMEOUT_SECS=10

set -o errexit
set -o nounset
set -o pipefail

export PATH="$(dirname "$0"):$PATH"

# default is to connect
action="Connect"
preposition="to"
while [ "${1:-}" ]
do
  if [ "$1" = "-h" ]
  then
    echo "Usage: $0 [ -h ] [ -d (disconnect) ] [ <device name (default: $DEFAULT_DEVICE_NAME)> ]"
    exit 2
  elif [ "$1" = "-d" ]
  then
    action="Disconnect"
    preposition="from"
  else
    DEVICE_NAME="$1"
  fi
  shift
done
echo "${action}ing $preposition $DEVICE_NAME"

if which blueutil > /dev/null 2>&1
then
  blueutil --power=1
fi

if ! which -s lsbt
then
  echo "Can't find lsbt executable"
  exit 4
fi

if ! lsbt > /dev/null 2>&1 < /dev/null
then
  echo "Can't run lsbt executable (no xmlstarlet?)"
  exit 9
fi

if [ "$action" = "Disconnect" ]
then
  # error if trying to disconnect and it's not connected
  if [ ! "$(lsbt -c "$DEVICE_NAME")" ]
  then
    echo "Doesn't look like device is connected: $DEVICE_NAME"
    exit 5
  fi
else
  # error if trying to connect and it's already connected
  if [ "$(lsbt -c "$DEVICE_NAME")" ]
  then
    echo "Looks like device is already connected: $DEVICE_NAME"
    exit 6
  fi
fi

osascript  <<END
-- activate application "SystemUIServer"
tell application "System Events"
	tell process "SystemUIServer"
		-- Working CONNECT/DISCONNECT Script.  Goes through the following:
		-- Clicks on Bluetooth Menu (OSX Top Menu Bar)
		--    => Clicks on $DEVICE_NAME Item
		--      => Clicks on $action Item
		get every menu bar
		set btMenu to (menu bar item 1 of menu bar 1 where description is "bluetooth")
		tell btMenu
			click
		end tell
		tell menu 1 of btMenu
			if exists menu item "$DEVICE_NAME" then
				set deviceMenu to (menu item "$DEVICE_NAME")
				tell (menu item "$DEVICE_NAME")
					click
					if exists menu item "$action" of menu 1 then
						click menu item "$action" of menu 1
						return "${action}ing..."
					else
						click btMenu -- Close main BT drop down if $action wasn\'t present
						return "$action menu item was not found, are you already in desired state??"
					end if
				end tell
			else
        return "Device menu was not found, are headphones paired and not already connecting/disconnecting?"
			end if
		end tell
	end tell
end tell
END

echo -n "Watching to see change in lsbt output..."
stop_looking_for_change_at=$(expr $(date +%s) + $TIMEOUT_SECS)
saw_change=""
while [ ! "$saw_change" -a "$(date +%s)" -lt $stop_looking_for_change_at ]
do
  echo -n .
  if [ "$action" = "Disconnect" ]
  then
    # We're done once it's not connected
    if [ ! "$(lsbt -c "$DEVICE_NAME")" ]
    then
      echo
      echo "Disconnected!"
      saw_change=1
    fi
  else
    # We're done once it's connected
    if [ "$(lsbt -c "$DEVICE_NAME")" ]
    then
      echo
      echo "Connected!"
      saw_change=1
    fi
  fi
done
if [ ! "$saw_change" ]
then
  echo
  echo "Timed out waiting for action"
  exit 7
fi
