#!/bin/bash
#
# Test a directory of files for correct syntax by examining #! header lines
# and file extensions.
#
# Skip files without clear validity criteria (unknown file types or text)
#
#
# Files aren't executed but are passed through a parser of their format
# to verify syntax only
#
# Types supported:
# Perl
# Python
# Javascript
# JSON
# Markdown
# Bourne Shell
#

set -o errexit
errors=0
files=0

export PATH=$PATH:./node_modules/.bin

for file in *
do
  let files=files+1
  echo "Testing file: $file"
  if [ -d "$file" ] 
  then
    echo Skipping directory
  elif [ "$file" = "gpgexport" ]
  then
    echo Skipping gpgexport
  elif echo "$file" | grep -q \\.as$
  then
    echo Skipping Applescript file
  elif head -1 "$file" | grep -q sh || echo "$file" | grep -q \\.sh$ || echo "$file" | grep -q \\.env$
  then
    if ! bash -n "$file"
    then
      let errors=errors+1
      echo ERROR: syntax check failed
    fi
  elif head -1 "$file" | grep -q perl || echo "$file" | grep -q \\.pl$
  then
    if ! perl -c "$file"
    then
      let errors=errors+1
      echo ERROR: syntax check failed
      fi
  elif head -1 "$file" | grep -q python || echo "$file" | grep -q \\.py$
  then
    if ! python -m py_compile "$file"
    then
      let errors=errors+1
      echo ERROR: syntax check failed
      fi
  elif echo "$file" | grep -q \\.json$
  then
    if ! cat "$file" | python -mjson.tool > /dev/null
    then
      let errors=errors+1
      echo ERROR: syntax check failed
    fi
  elif echo "$file" | grep -q \\.md$
  then
    if ! cat "$file" | md2html > /dev/null
    then
      let errors=errors+1
      echo ERROR: syntax check failed
    fi
  elif head -1 "$file" | grep -q node || echo "$file" | grep -q \\.js$
  then
    if ! tail -n +2 "$file" | uglifyjs > /dev/null
    then
      let errors=errors+1
      echo ERROR: syntax check failed
    fi
  elif echo "$file" | grep -q \\.pyc$
  then
    echo Skipping compiled python file
  elif echo "$file" | grep -q \\.txt$
  then
    echo Skipping text file
  else
    let errors=errors+1
    echo "ERROR: Unknown file type"
  fi
done

echo "Examined $files files"
echo "Found $errors errors"
if [ $errors -gt 0 ] 
then
  exit $errors
else
  exit 0
fi
