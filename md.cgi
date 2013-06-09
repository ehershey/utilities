#!/bin/sh

file="$QUERY_STRING"
if [ ! "`echo \"$file\" | grep ^/`" ]
then
  file=`pwd`"/$file"
fi
echo "Content-Type: text/html"
echo
echo "reading $file" >&2
/usr/local/bin/markdown_py < "$file"
