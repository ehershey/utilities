#!/bin/bash
#
# Connect bluetooth audio device in osx
#
#
# Use applescript to navigate bluetooth menu bar and select "Connect" 
# in the submenu named in this variable:
DEVICE_NAME="ODT Privates"

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
