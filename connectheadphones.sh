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
DEVICE_NAME=${1:-${BLUETOOTH_AUDIO_DEVICE_NAME:-$DEFAULT_DEVICE_NAME}}

if [[ "$DEVICE_NAME" = "-h" ]]
then
  echo "Usage: $0 [ <device name (default: $DEFAULT_DEVICE_NAME)> ]"
else
  echo "Connecting to $DEVICE_NAME"
fi

if which blueutil > /dev/null 2>&1
then
  blueutil --power=1
fi

osascript  <<END
-- activate application "SystemUIServer"
tell application "System Events"
	tell process "SystemUIServer"
		-- Working CONNECT Script.  Goes through the following:
		-- Clicks on Bluetooth Menu (OSX Top Menu Bar)
		--    => Clicks on $DEVICE_NAME Item
		--      => Clicks on Connect Item
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
					if exists menu item "Connect" of menu 1 then
						click menu item "Connect" of menu 1
						return "Connecting..."
					else
						click btMenu -- Close main BT drop down if Connect wasn\'t present
						return "Connect menu was not found, are you already connected?"
					end if
				end tell
			else
				return "Device menu was not found, are headphones paired and not already connecting?"
			end if
		end tell
	end tell
end tell
END
