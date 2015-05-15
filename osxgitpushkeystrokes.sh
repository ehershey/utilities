#!/bin/sh
#
# TODO - eat multiple event triggers
#
BRANCH=v3.0
date >> /tmp/button.log
osascript -e 'tell application "System Events" to keystroke "git push origin $BRANCH\n"'
date >> /tmp/button.log
