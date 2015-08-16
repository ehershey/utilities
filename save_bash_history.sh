#!/bin/bash
#
#
# Copy bash history to Dropbox
#
#
set +x
cp -pri ~/.bash_history ~/Dropbox/Misc/bash_history/bash_history-$(date +%Y%m%d-$(hostname))
