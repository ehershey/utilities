#!/bin/sh
#
# TODO - eat multiple event triggers
#
date >> /tmp/button.log
osascript -e 'tell application "System Events" to keystroke "\n"'
date >> /tmp/button.log
