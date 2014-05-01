#!/bin/sh
# Copy reminders from Reminders.app, paste to stdin, script will output
# the number of incomplete reminders are in the selected list. 
# 

grep '\[ \]' | wc -l
