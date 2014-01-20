#!/bin/bash
# Markdown processor CGI script for OS X
#
# To install: 
# 1) Copy to cgi-bin or equivalent - e.g. 
#    sudo cp /Users/ernie/git/utilities/md.cgi /Library/WebServer/CGI-Executables/
#    OR - run md.cgi --install
# 2) Create shell alias for opening markdown files - see openmd() below
#

if [ "$1" -a "$1" = "--install" ]
then
  set -x
  sudo cp $0 /Library/WebServer/CGI-Executables/
  set +x
  tempfile=$(mktemp /tmp/openmd.XXXXXX)
  cat >>$tempfile <<-'EOF'

  openmd() {
    fullpath="$1"
    if [ ! "$(echo "$fullpath" | grep ^/)" ]
    then
      fullpath="$PWD/$fullpath"
    fi
    if [ ! -f "$fullpath" ]
    then
      echo "Path doesn't exist: $fullpath"
      return 2
    fi
    open "http://localhost/cgi-bin/md.cgi?$fullpath"
  }
EOF
  echo "# to load openmd() shell function:"
  echo "source $tempfile"
  exit
fi
file="$QUERY_STRING"
echo "Content-Type: text/html"
echo
echo "reading $file" >&2
modtime=$(localtime $(stat -f%m $file))

echo "<html><head><title>$file ($modtime) </title></head><body>"

export PATH=$PATH:/usr/local/bin

if [ ! -r "$file" ]
then
  echo "Can't find file: $file"
elif [ "$REMOTE_ADDR" != "::1" -a "$REMOTE_ADDR" != "127.0.0.1" ]
then
  echo "Can only serve files to localhost (REMOTE_ADDR=$REMOTE_ADDR)"
# look for different parsers
#
elif which -s markdown_py 
then
  markdown_py < "$file"
elif which -s markdown2
then
  markdown2 < "$file"
elif which -s markdown
then
  markdown < "$file"
else
  echo "Can't find a markdown parser"
fi
echo "</body></html>"

