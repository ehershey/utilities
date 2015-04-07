#!/bin/sh
date >> /tmp/button.log
osascript -e 'tell application "System Events" to keystroke "echo git push origin master\n"'
date >> /tmp/button.log
